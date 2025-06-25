from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from uuid import UUID

from app.api.v1.auth.models import User
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.schemas.schemas import UserResponseModel as UserResponse
from app.api.v1.auth.services.service import ActivityService
from app.core.database import async_get_db
from app.core.websocket import ConnectionManager
from .schemas import NotificationCreate, NotificationResponse, NotificationUserResponse, UnreadNotificationResponse
from .service import NotificationService
from sqlalchemy import select


notification_router = APIRouter()
notification_service = NotificationService()


manager = ConnectionManager()


@notification_router.get("/user/unread", response_model=List[UnreadNotificationResponse])
async def get_unread_notifications(
    db: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve unread notifications for the current user."""
    return await notification_service.get_unread_notifications(user_id=current_user.id, session=db)


@notification_router.get("/{notification_id}/mark-as-read", response_model=UnreadNotificationResponse)
async def mark_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Mark a notification as read."""
    notification = await notification_service.mark_notification_as_read(notification_id=notification_id, user_id=current_user.id, session=db)
    if not notification:
        raise HTTPException(
            status_code=404, detail="Notification not found or already read.")
    return notification


@notification_router.get("/all", response_model=List[NotificationResponse])
async def get_all_notifications(
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Retrieve all notifications for the current user."""
    notifications = await notification_service.get_all_notifications(session=db)
    return notifications


@notification_router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID ):
    """WebSocket endpoint for real-time notifications."""
    await manager.connect(user_id, websocket, "notifications")
    try:
        while True:
            await websocket.receive_text()  # Keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket, "notifications")


async def broadcast_notification(notification: UnreadNotificationResponse):
    """Broadcast a notification to all connected users."""
    for user in notification.recipients:
        await manager.send_notification(user.id, "notifications", notification.model_dump())


@notification_router.post("/send_notification", response_model=dict)
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    user_ids: List[UUID] = [],
    db: AsyncSession = Depends(async_get_db),
    _: UserResponse = Depends(get_current_user)
):
    """Create a new notification and send it to specified users."""
    if not user_ids:
        statement = select(User)
        result = await db.execute(statement)
        users = result.scalars().all()
        user_ids = [user.id for user in users]
    else:
        # If user_ids are provided, fetch those users' info for the schema
        statement = select(User).where(User.id.in_(user_ids))
        result = await db.execute(statement)
        users = result.scalars().all()

    # Store the notification in the DB
    saved_notification = await notification_service.store_notification(
        notification_data=notification,
        user_ids=user_ids,
        session=db
    )

    response = UnreadNotificationResponse(
        id=saved_notification.id,
        sender_id=saved_notification.sender_id,
        title=saved_notification.title,
        message=saved_notification.message,
        created_at=saved_notification.created_at,
        is_read=False
    )

    # Send notification in the background
    background_tasks.add_task(broadcast_notification, response)
    return {"detail": "Notification sent successfully."}
