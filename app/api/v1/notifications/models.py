from typing import List, Optional, TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from sqlalchemy import Table, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User  # Avoid circular import


# Association Table with read status
notification_recipients = Table(
    "notification_recipients",
    Base.metadata,
    Column("notification_id", UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("is_read", Boolean, default=False, nullable=False),
)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender: Mapped[Optional["User"]] = relationship("User", back_populates="sent_notifications", passive_deletes=True)
    recipients: Mapped[List["User"]] = relationship(
        "User",
        secondary=notification_recipients,
        back_populates="notifications_received",
        passive_deletes=True,
    )
