from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from uuid import UUID
from typing import List
from .models import Notification, notification_recipients
from .schemas import NotificationCreate, NotificationResponse, NotificationUserResponse, UnreadNotificationResponse
from sqlalchemy import update, desc


class NotificationService:
    async def store_notification(self, notification_data: NotificationCreate, user_ids: List[UUID], session: AsyncSession) -> Notification:
        """Create and store a new notification, and assign recipients."""
        # Create the notification object
        notification = Notification(
            sender_id=notification_data.sender_id,
            title=notification_data.title,
            message=notification_data.message
        )

        session.add(notification)
        await session.commit()
        await session.refresh(notification)

        # Add recipients
        for user_id in user_ids:
            await session.execute(
                notification_recipients.insert().values(
                    notification_id=notification.id,
                    user_id=user_id,
                    is_read=False  # Initially unread
                )
            )
        await session.commit()
        return notification

    async def get_unread_notifications(self, user_id: UUID, session: AsyncSession) -> List[UnreadNotificationResponse]:
        """Retrieve unread notifications for a user."""
        statement = select(Notification).join(notification_recipients).filter(
            notification_recipients.c.user_id == user_id,
            notification_recipients.c.is_read == False
        ).options(joinedload(Notification.recipients)).order_by(desc(Notification.created_at))  # This will load recipients if needed
        result = await session.execute(statement)
        notifications = result.scalars().all()

        return [UnreadNotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            created_at=notification.created_at,
            is_read=False  # All notifications fetched are unread
        ) for notification in notifications]

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID, session: AsyncSession) -> UnreadNotificationResponse | None:
        """Mark a notification as read for a specific user and return the updated notification."""

        statement = select(notification_recipients).filter(
            notification_recipients.c.notification_id == notification_id,
            notification_recipients.c.user_id == user_id
        )
        result = await session.execute(statement)
        recipient = result.first()

        if not recipient:
            raise HTTPException(
                status_code=404, detail="Notification or User not found")

        # Update the read status using an update statement
        await session.execute(
            update(notification_recipients)
            .where(
                notification_recipients.c.notification_id == notification_id,
                notification_recipients.c.user_id == user_id
            )
            .values(is_read=True)
        )
        await session.commit()

        # Return the updated notification
        updated_notification = await session.execute(
            select(Notification).filter(Notification.id == notification_id)
        )
        notification = updated_notification.scalar_one_or_none()
        return UnreadNotificationResponse(
            id=notification.id,
            title=notification.title,
            message=notification.message,
            created_at=notification.created_at,
            is_read=True  # Marked as read
        ) if notification else None

    async def get_all_notifications(self, session: AsyncSession) -> List[NotificationResponse]:
        """Retrieve all notifications with recipient user details."""
        statement = select(Notification).options(joinedload(
            Notification.recipients)).order_by(desc(Notification.created_at))
        result = await session.execute(statement)
        notifications = result.scalars().all()

        responses = []
        for notification in notifications:
            recipient_schemas = [
                NotificationUserResponse(
                    id=recipient.id,
                    first_name=recipient.first_name,
                    last_name=recipient.last_name if recipient.last_name else "",
                    image_url=recipient.image_url,
                )
                for recipient in notification.recipients
            ]

            responses.append(NotificationResponse(
                id=notification.id,
                sender_id=notification.sender_id,
                title=notification.title,
                message=notification.message,
                created_at=notification.created_at,
                recipients=recipient_schemas
            ))

        return responses
