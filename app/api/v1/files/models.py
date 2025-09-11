from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base
if TYPE_CHECKING:
    from app.api.v1.auth.models import User  # Avoid circular import



class FileType(str, Enum):
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"

class FileActivityAction(str, Enum):
    UPLOADED = "uploaded"
    MODIFIED = "modified"
    ARCHIVED = "archived"
    DELETED = "deleted"
    SHARED = "shared"

class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[FileType] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)  # Size in bytes
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")
    activities: Mapped[List["FileActivity"]] = relationship("FileActivity", back_populates="file", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "file_name", name="unique_user_file_name"),)

class FileActivity(Base):
    __tablename__ = "file_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    action: Mapped[FileActivityAction] = mapped_column(String, nullable=False)  # e.g., "uploaded", "modified", etc.
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    file: Mapped["File"] = relationship("File", back_populates="activities")


class Storage(Base):
    __tablename__ = "storage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    total_space: Mapped[int] = mapped_column(nullable=False)  # Total space in bytes
    used_space: Mapped[int] = mapped_column(default=0, nullable=False)  # Used space in bytes
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="storage")