"""
WebSocket connection manager for real-time updates
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """
    WebSocket connection manager

    Manages WebSocket connections for real-time updates.
    Supports:
    - Per-user connections
    - Per-organization connections
    - Broadcasting to multiple connections
    - Event subscriptions
    """

    def __init__(self):
        # Active connections by user_id
        self.user_connections: Dict[int, Set[WebSocket]] = {}

        # Active connections by organization_id
        self.org_connections: Dict[int, Set[WebSocket]] = {}

        # Connection subscriptions (connection -> set of event types)
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        organization_id: int = None
    ):
        """
        Accept and register a WebSocket connection

        Args:
            websocket: WebSocket connection
            user_id: User ID
            organization_id: Optional organization ID
        """
        await websocket.accept()

        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        # Add to organization connections
        if organization_id:
            if organization_id not in self.org_connections:
                self.org_connections[organization_id] = set()
            self.org_connections[organization_id].add(websocket)

        # Initialize subscriptions
        self.subscriptions[websocket] = set()

        # Store metadata
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "organization_id": organization_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        # Get metadata
        metadata = self.connection_metadata.get(websocket, {})
        user_id = metadata.get("user_id")
        organization_id = metadata.get("organization_id")

        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove from organization connections
        if organization_id and organization_id in self.org_connections:
            self.org_connections[organization_id].discard(websocket)
            if not self.org_connections[organization_id]:
                del self.org_connections[organization_id]

        # Remove subscriptions
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to specific connection

        Args:
            message: Message dictionary
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def send_to_user(self, message: dict, user_id: int):
        """
        Send message to all connections of a specific user

        Args:
            message: Message dictionary
            user_id: Target user ID
        """
        connections = self.user_connections.get(user_id, set())

        for connection in list(connections):  # Use list() to avoid modification during iteration
            await self.send_personal_message(message, connection)

    async def send_to_organization(self, message: dict, organization_id: int):
        """
        Send message to all connections of a specific organization

        Args:
            message: Message dictionary
            organization_id: Target organization ID
        """
        connections = self.org_connections.get(organization_id, set())

        for connection in list(connections):
            await self.send_personal_message(message, connection)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all active connections

        Args:
            message: Message dictionary
        """
        for connections in self.user_connections.values():
            for connection in list(connections):
                await self.send_personal_message(message, connection)

    async def broadcast_event(self, event_type: str, data: dict):
        """
        Broadcast event to subscribed connections

        Args:
            event_type: Event type (e.g., "api_call", "payment", "webhook")
            data: Event data
        """
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all connections subscribed to this event type
        for websocket, subscriptions in self.subscriptions.items():
            if "*" in subscriptions or event_type in subscriptions:
                await self.send_personal_message(message, websocket)

    def subscribe(self, websocket: WebSocket, event_types: List[str]):
        """
        Subscribe connection to event types

        Args:
            websocket: WebSocket connection
            event_types: List of event types to subscribe to
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(event_types)

    def unsubscribe(self, websocket: WebSocket, event_types: List[str]):
        """
        Unsubscribe connection from event types

        Args:
            websocket: WebSocket connection
            event_types: List of event types to unsubscribe from
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].difference_update(event_types)

    async def send_user_activity(self, user_id: int, activity_type: str, data: dict):
        """
        Send user activity notification

        Args:
            user_id: User ID
            activity_type: Activity type
            data: Activity data
        """
        message = {
            "type": "activity",
            "activity_type": activity_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(message, user_id)

    async def send_api_usage_update(self, user_id: int, usage_data: dict):
        """
        Send real-time API usage update

        Args:
            user_id: User ID
            usage_data: Usage statistics
        """
        message = {
            "type": "api_usage",
            "data": usage_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(message, user_id)

    async def send_webhook_delivery_update(self, user_id: int, delivery_data: dict):
        """
        Send webhook delivery status update

        Args:
            user_id: User ID
            delivery_data: Delivery information
        """
        message = {
            "type": "webhook_delivery",
            "data": delivery_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(message, user_id)

    async def send_payment_notification(self, user_id: int, payment_data: dict):
        """
        Send payment notification

        Args:
            user_id: User ID
            payment_data: Payment information
        """
        message = {
            "type": "payment",
            "data": payment_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(message, user_id)

    async def send_system_notification(self, user_id: int, notification: dict):
        """
        Send system notification

        Args:
            user_id: User ID
            notification: Notification data
        """
        message = {
            "type": "notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.send_to_user(message, user_id)

    def get_active_connections_count(self) -> int:
        """Get total active connections count"""
        return sum(len(connections) for connections in self.user_connections.values())

    def get_user_connections_count(self, user_id: int) -> int:
        """Get connection count for specific user"""
        return len(self.user_connections.get(user_id, set()))

    async def ping_all_connections(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }

        for connections in self.user_connections.values():
            for connection in list(connections):
                await self.send_personal_message(ping_message, connection)

                # Update last ping time
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["last_ping"] = datetime.utcnow()


# Global connection manager instance
manager = ConnectionManager()


async def start_ping_task():
    """Background task to ping all connections every 30 seconds"""
    while True:
        await asyncio.sleep(30)
        await manager.ping_all_connections()
