"""
Organization Service - Business logic for multi-tenancy and organization management
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets
from slugify import slugify

from app.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    OrganizationRole,
    OrganizationStatus,
    User
)
from app.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationInviteCreate,
    OrganizationMemberUpdate,
    PaginationParams
)
from app.core.cache import RedisCache, cache, invalidate_cache


class OrganizationService:
    """Service for organization operations"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        org_data: OrganizationCreate
    ) -> Organization:
        """Create a new organization"""
        # Generate slug if not provided
        slug = org_data.slug or slugify(org_data.name)

        # Check if slug is taken
        existing = await OrganizationService.get_by_slug(db, slug)
        if existing:
            # Add random suffix if slug exists
            slug = f"{slug}-{secrets.token_hex(4)}"

        # Create organization
        organization = Organization(
            name=org_data.name,
            slug=slug,
            description=org_data.description,
            website=org_data.website,
            status=OrganizationStatus.ACTIVE,
        )

        db.add(organization)
        await db.commit()
        await db.refresh(organization)

        # Add creator as owner
        member = OrganizationMember(
            user_id=user_id,
            organization_id=organization.id,
            role=OrganizationRole.OWNER,
            is_active=True
        )

        db.add(member)
        await db.commit()

        return organization

    @staticmethod
    @cache(key_prefix="org", expire=3600)
    async def get_by_id(db: AsyncSession, org_id: int) -> Optional[Organization]:
        """Get organization by ID (cached)"""
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        result = await db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_organizations(
        db: AsyncSession,
        user_id: int,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Organization], int]:
        """List organizations user is a member of"""
        query = (
            select(Organization)
            .join(OrganizationMember)
            .where(
                and_(
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.is_active == True
                )
            )
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date
        query = query.order_by(Organization.created_at.desc())

        # Execute
        result = await db.execute(query)
        organizations = result.scalars().all()

        return list(organizations), total

    @staticmethod
    @invalidate_cache(key_prefix="org")
    async def update(
        db: AsyncSession,
        org_id: int,
        org_data: OrganizationUpdate
    ) -> Organization:
        """Update organization"""
        organization = await OrganizationService.get_by_id(db, org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Update fields
        update_data = org_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)

        await db.commit()
        await db.refresh(organization)

        return organization

    @staticmethod
    @invalidate_cache(key_prefix="org")
    async def delete(db: AsyncSession, org_id: int) -> bool:
        """Delete organization (soft delete)"""
        organization = await OrganizationService.get_by_id(db, org_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        organization.status = OrganizationStatus.DELETED
        await db.commit()

        return True

    # Member Management

    @staticmethod
    async def get_member(
        db: AsyncSession,
        organization_id: int,
        user_id: int
    ) -> Optional[OrganizationMember]:
        """Get organization member"""
        result = await db.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_members(
        db: AsyncSession,
        organization_id: int,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[OrganizationMember], int]:
        """List organization members"""
        query = select(OrganizationMember).where(
            and_(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_active == True
            )
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date
        query = query.order_by(OrganizationMember.created_at.desc())

        # Execute
        result = await db.execute(query)
        members = result.scalars().all()

        return list(members), total

    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        organization_id: int,
        user_id: int,
        new_role: OrganizationRole
    ) -> OrganizationMember:
        """Update member's role in organization"""
        member = await OrganizationService.get_member(db, organization_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )

        # Cannot change owner role
        if member.role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change owner's role"
            )

        member.role = new_role
        await db.commit()
        await db.refresh(member)

        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        organization_id: int,
        user_id: int
    ) -> bool:
        """Remove member from organization"""
        member = await OrganizationService.get_member(db, organization_id, user_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )

        # Cannot remove owner
        if member.role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove owner from organization"
            )

        # Soft delete
        member.is_active = False
        await db.commit()

        return True

    # Invitation Management

    @staticmethod
    async def create_invitation(
        db: AsyncSession,
        organization_id: int,
        invited_by_id: int,
        invitation_data: OrganizationInviteCreate
    ) -> OrganizationInvitation:
        """Create organization invitation"""
        # Check if organization exists
        organization = await OrganizationService.get_by_id(db, organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Check if user is already a member
        existing_member = await OrganizationService.get_member_by_email(
            db, organization_id, invitation_data.email
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization"
            )

        # Check if there's already a pending invitation
        existing_invitation = await OrganizationService.get_pending_invitation(
            db, organization_id, invitation_data.email
        )
        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already sent to this email"
            )

        # Generate invitation token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create invitation
        invitation = OrganizationInvitation(
            organization_id=organization_id,
            invited_by_id=invited_by_id,
            email=invitation_data.email,
            role=invitation_data.role,
            token=token,
            expires_at=expires_at,
            accepted=False
        )

        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)

        # TODO: Send invitation email
        # await EmailService.send_organization_invitation(invitation)

        return invitation

    @staticmethod
    async def get_member_by_email(
        db: AsyncSession,
        organization_id: int,
        email: str
    ) -> Optional[OrganizationMember]:
        """Get member by email"""
        result = await db.execute(
            select(OrganizationMember)
            .join(User)
            .where(
                and_(
                    OrganizationMember.organization_id == organization_id,
                    User.email == email,
                    OrganizationMember.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_pending_invitation(
        db: AsyncSession,
        organization_id: int,
        email: str
    ) -> Optional[OrganizationInvitation]:
        """Get pending invitation"""
        result = await db.execute(
            select(OrganizationInvitation).where(
                and_(
                    OrganizationInvitation.organization_id == organization_id,
                    OrganizationInvitation.email == email,
                    OrganizationInvitation.accepted == False,
                    OrganizationInvitation.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def accept_invitation(
        db: AsyncSession,
        token: str,
        user_id: int
    ) -> OrganizationMember:
        """Accept organization invitation"""
        # Get invitation
        result = await db.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.token == token
            )
        )
        invitation = result.scalar_one_or_none()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        # Check if already accepted
        if invitation.accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation already accepted"
            )

        # Check if expired
        if invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )

        # Verify user email matches invitation
        user = await db.get(User, user_id)
        if not user or user.email != invitation.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation was sent to a different email address"
            )

        # Check if user is already a member
        existing_member = await OrganizationService.get_member(
            db, invitation.organization_id, user_id
        )
        if existing_member and existing_member.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of this organization"
            )

        # Create or reactivate membership
        if existing_member:
            existing_member.is_active = True
            existing_member.role = invitation.role
            member = existing_member
        else:
            member = OrganizationMember(
                user_id=user_id,
                organization_id=invitation.organization_id,
                role=invitation.role,
                is_active=True
            )
            db.add(member)

        # Mark invitation as accepted
        invitation.accepted = True
        invitation.accepted_at = datetime.utcnow()

        await db.commit()
        await db.refresh(member)

        return member

    @staticmethod
    async def check_permission(
        db: AsyncSession,
        organization_id: int,
        user_id: int,
        required_role: OrganizationRole
    ) -> bool:
        """Check if user has required role in organization"""
        member = await OrganizationService.get_member(db, organization_id, user_id)

        if not member or not member.is_active:
            return False

        # Role hierarchy: OWNER > ADMIN > MEMBER > VIEWER
        role_hierarchy = {
            OrganizationRole.OWNER: 4,
            OrganizationRole.ADMIN: 3,
            OrganizationRole.MEMBER: 2,
            OrganizationRole.VIEWER: 1,
        }

        return role_hierarchy.get(member.role, 0) >= role_hierarchy.get(required_role, 0)

    @staticmethod
    async def get_organization_stats(
        db: AsyncSession,
        organization_id: int
    ) -> dict:
        """Get organization statistics"""
        # Member count
        member_result = await db.execute(
            select(func.count(OrganizationMember.id))
            .where(
                and_(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.is_active == True
                )
            )
        )
        member_count = member_result.scalar_one()

        # TODO: Add more stats (API keys, webhooks, API calls, etc.)

        return {
            "organization_id": organization_id,
            "member_count": member_count,
            "active_members": member_count,  # All active members
        }
