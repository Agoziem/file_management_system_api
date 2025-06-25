from pydantic import BaseModel, UUID4, field_serializer
from datetime import datetime
from typing import List


class NotificationBase(BaseModel):
    """Base schema for Notification"""
    sender_id: UUID4 | None = None  # Admin sender
    title: str
    message: str


class NotificationCreate(NotificationBase):
    """Schema for creating a new Notification"""
    pass

class NotificationUserResponse(BaseModel):
    """Schema for returning User details"""
    id: UUID4
    first_name: str
    last_name: str
    image_url: str | None

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

class NotificationResponse(NotificationBase):
    """Schema for returning Notification details"""
    id: UUID4
    created_at: datetime
    recipients: List[NotificationUserResponse]  # List of recipients

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()


class UnreadNotificationResponse(NotificationBase):
    """Schema for a single unread notification"""
    id: UUID4
    created_at: datetime
    is_read: bool

    @field_serializer("id")
    def serialize_uuid(self, value: UUID4) -> str:
        return str(value)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()



class NotificationReadUpdate(BaseModel):
    """Schema for updating the read status of a notification"""
    notification_id: UUID4
    user_id: UUID4
    is_read: bool

    @field_serializer("notification_id")
    def serialize_notification_id(self, value: UUID4) -> str:
        return str(value)
