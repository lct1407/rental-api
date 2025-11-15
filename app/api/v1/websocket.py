"""
WebSocket API endpoints - Real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.websocket import manager
from app.core.security import SecurityManager
from app.services.user_service import UserService
from app.models import User, UserStatus
import json


router = APIRouter(tags=["WebSocket"])


async def get_websocket_user(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Authenticate WebSocket connection using JWT token

    Args:
        websocket: WebSocket connection
        token: JWT access token from query parameter
        db: Database session

    Returns:
        Authenticated user

    Raises:
        WebSocketDisconnect: If authentication fails
    """
    try:
        # Decode token
        payload = SecurityManager.decode_token(token)

        # Check token type
        if payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token type")
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

        # Get user
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

        user = await UserService.get_by_id(db, user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"User account is {user.status.value}")
            raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

        return user

    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)


@router.websocket("/ws/realtime")
async def websocket_realtime_updates(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time updates

    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime?token=YOUR_JWT_TOKEN');
    ```

    **Authentication:**
    - Pass JWT access token as query parameter

    **Message Types Received:**
    - `connection`: Connection established
    - `event`: Subscribed event occurred
    - `activity`: User activity notification
    - `api_usage`: API usage update
    - `webhook_delivery`: Webhook delivery status
    - `payment`: Payment notification
    - `notification`: System notification
    - `ping`: Keep-alive ping

    **Message Types to Send:**
    - Subscribe to events:
      ```json
      {
        "action": "subscribe",
        "events": ["api_call", "payment", "webhook_delivery"]
      }
      ```
    - Unsubscribe from events:
      ```json
      {
        "action": "unsubscribe",
        "events": ["api_call"]
      }
      ```
    - Pong (response to ping):
      ```json
      {
        "action": "pong"
      }
      ```

    **Available Events:**
    - `api_call`: API calls made
    - `payment`: Payment processed
    - `webhook_delivery`: Webhook delivered
    - `subscription`: Subscription changes
    - `api_key`: API key changes
    - `credit`: Credit balance changes
    - `*`: All events (wildcard)
    """
    # Authenticate user
    user = await get_websocket_user(websocket, token, db)

    # Connect to manager
    await manager.connect(websocket, user.id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    # Subscribe to events
                    events = message.get("events", [])
                    manager.subscribe(websocket, events)

                    await manager.send_personal_message(
                        {
                            "type": "subscription_update",
                            "action": "subscribed",
                            "events": events
                        },
                        websocket
                    )

                elif action == "unsubscribe":
                    # Unsubscribe from events
                    events = message.get("events", [])
                    manager.unsubscribe(websocket, events)

                    await manager.send_personal_message(
                        {
                            "type": "subscription_update",
                            "action": "unsubscribed",
                            "events": events
                        },
                        websocket
                    )

                elif action == "pong":
                    # Respond to ping
                    pass

                else:
                    # Unknown action
                    await manager.send_personal_message(
                        {
                            "type": "error",
                            "message": f"Unknown action: {action}"
                        },
                        websocket
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "Invalid JSON"
                    },
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/analytics")
async def websocket_analytics(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analytics

    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analytics?token=YOUR_JWT_TOKEN');
    ```

    **Updates Sent:**
    - Real-time API call metrics
    - Response time statistics
    - Error rate updates
    - Request per second (RPS)
    - Active API keys usage

    **Update Frequency:** Every 5 seconds
    """
    # Authenticate user
    user = await get_websocket_user(websocket, token, db)

    # Connect to manager
    await manager.connect(websocket, user.id)

    try:
        import asyncio
        from app.services.analytics_service import AnalyticsService

        while True:
            # Get real-time metrics
            metrics = await AnalyticsService.get_real_time_metrics(db, user.id)

            # Send to client
            await manager.send_personal_message(
                {
                    "type": "analytics",
                    "data": metrics
                },
                websocket
            )

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/organization/{organization_id}")
async def websocket_organization(
    websocket: WebSocket,
    organization_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for organization-wide updates

    **Connection:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/organization/123?token=YOUR_JWT_TOKEN');
    ```

    **Authentication:**
    - User must be a member of the organization

    **Updates:**
    - Organization member activities
    - Shared API usage
    - Team notifications
    """
    # Authenticate user
    user = await get_websocket_user(websocket, token, db)

    # Verify organization membership
    from app.services.organization_service import OrganizationService

    is_member = await OrganizationService.is_member(db, organization_id, user.id)
    if not is_member:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not a member of this organization")
        raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION)

    # Connect to manager
    await manager.connect(websocket, user.id, organization_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "broadcast":
                    # Broadcast message to all organization members
                    broadcast_data = message.get("data", {})

                    await manager.send_to_organization(
                        {
                            "type": "broadcast",
                            "from_user_id": user.id,
                            "data": broadcast_data
                        },
                        organization_id
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": "Invalid JSON"
                    },
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/ws/stats")
async def get_websocket_stats(current_user: User = Depends(get_websocket_user)):
    """
    Get WebSocket connection statistics

    **Note:** This is a regular HTTP endpoint, not WebSocket

    **Returns:**
    - Total active connections
    - Connections per user
    - Connection metadata
    """
    # This requires authentication dependency adjustment
    # For now, return basic stats

    return {
        "total_connections": manager.get_active_connections_count(),
        "user_connections": {
            user_id: len(connections)
            for user_id, connections in manager.user_connections.items()
        }
    }
