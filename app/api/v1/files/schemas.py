from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

from app.api.v1.files.models import FileType


class FileBase(BaseModel):
    file_name: str
    file_type: FileType


class FileCreate(FileBase):
    file_size: int
    file_url: str


class FileResponse(FileBase):
    id: UUID
    user_id: UUID
    file_size: int
    file_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileUpdate(BaseModel):
    file_name: Optional[str] = None


class FileList(BaseModel):
    items: List[FileResponse]
    count: int


class StorageBase(BaseModel):
    total_space: int
    used_space: int = 0


class StorageCreate(StorageBase):
    user_id: UUID


class StorageResponse(StorageBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class StorageUpdate(BaseModel):
    total_space: Optional[int] = None
    used_space: Optional[int] = None


class FileUploadResponse(BaseModel):
    url: str
    file_id: UUID
    status: str = "success"


class FileDeleteResponse(BaseModel):
    status: str = "deleted"


class MultipleFileUploadResponse(BaseModel):
    urls: List[str]
    file_ids: List[UUID]
    status: str = "success"


# Analytics Schemas
class FileTypeDistribution(BaseModel):
    type_distribution: dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "type_distribution": {
                    "image": 10,
                    "document": 15,
                    "video": 5,
                    "audio": 8,
                    "other": 3
                }
            }
        }


class StorageUsageTrend(BaseModel):
    storage_trends: dict[str, List]

    class Config:
        json_schema_extra = {
            "example": {
                "storage_trends": {
                    "dates": ["2025-08-01", "2025-08-02", "2025-08-03"],
                    "file_counts": [5, 8, 12],
                    "sizes": [1048576, 2097152, 3145728]  # 1MB, 2MB, 3MB
                }
            }
        }


class FileActivity(BaseModel):
    id: UUID
    file_name: str
    file_type: FileType
    file_size: int
    updated_at: datetime
    created_at: datetime
    action: str


class RecentActivityResponse(BaseModel):
    recent_activity: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "recent_activity": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "file_name": "document.pdf",
                        "file_type": "document",
                        "file_size": 1048576,
                        "updated_at": "2025-08-19T10:00:00Z",
                        "created_at": "2025-08-19T10:00:00Z",
                        "action": "uploaded"
                    }
                ]
            }
        }


class LargeFile(BaseModel):
    id: UUID
    file_name: str
    file_type: FileType
    file_size: int
    size_mb: float
    created_at: datetime


class LargeFilesResponse(BaseModel):
    large_files: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "large_files": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "file_name": "video.mp4",
                        "file_type": "video",
                        "file_size": 52428800,
                        "size_mb": 50.0,
                        "created_at": "2025-08-19T10:00:00Z"
                    }
                ]
            }
        }


class FileAnalyticsDashboard(BaseModel):
    type_distribution: dict
    storage_trends: dict
    recent_activity: List[dict]
    large_files: List[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "type_distribution": {
                    "image": 10,
                    "document": 15,
                    "video": 5,
                    "audio": 8,
                    "other": 3
                },
                "storage_trends": {
                    "dates": ["2025-08-01", "2025-08-02", "2025-08-03"],
                    "file_counts": [5, 8, 12],
                    "sizes": [1048576, 2097152, 3145728]
                },
                "recent_activity": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "file_name": "document.pdf",
                        "file_type": "document",
                        "file_size": 1048576,
                        "updated_at": "2025-08-19T10:00:00Z",
                        "created_at": "2025-08-19T10:00:00Z",
                        "action": "uploaded"
                    }
                ],
                "large_files": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "file_name": "video.mp4",
                        "file_type": "video",
                        "file_size": 52428800,
                        "size_mb": 50.0,
                        "created_at": "2025-08-19T10:00:00Z"
                    }
                ]
            }
        }
