from fastapi import UploadFile, File, HTTPException, Form, APIRouter, Depends, Query, Path
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.auth.models import User
from app.core.database import async_get_db
from .models import FileType
from .schemas import (
    FileResponse, FileUpdate, FileList, StorageCreate, StorageResponse,
    FileUploadResponse, FileDeleteResponse, MultipleFileUploadResponse, StorageUpdate,
    FileTypeDistribution, StorageUsageTrend, RecentActivityResponse, 
    LargeFilesResponse, FileAnalyticsDashboard, FileActivityCreate, FileActivityResponse
)
from .services import (
    create_storage, get_file, get_files, update_file, delete_file, get_user_storage, update_storage,
    upload_and_create_file, determine_file_type, get_file_type_distribution,
    get_storage_usage_trends, get_recent_activity, get_large_files,
    create_file_activity, delete_file_activity, get_user_file_activities
)

file_router = APIRouter()

@file_router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    replace: bool = Form(True),
    key: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Upload a file to the storage. The file will be associated with the current user.
    If replace is True and a file with the same name exists, it will be replaced.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        # Determine file type from filename
        file_type = determine_file_type(file.filename)

        # Upload file and create record
        db_file = await upload_and_create_file(
            db, file, current_user.id, file_type, replace, key
        )
        
        return FileUploadResponse(
            url=db_file.file_url,
            file_id=db_file.id,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@file_router.post("/upload_multiple", response_model=MultipleFileUploadResponse)
async def upload_multiple(
    files: list[UploadFile] = File(...),
    replace: bool = Form(True),
    keys: list[str] = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Upload multiple files at once. Each file will be associated with the current user.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    elif any(not file.filename for file in files):
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        file_ids = []
        urls = []

        for file, key in zip(files, keys):

            # Validate file
            if not file.filename:
                break

            # Determine file type from filename
            file_type = determine_file_type(file.filename)
            
            # Upload file and create record
            db_file = await upload_and_create_file(
                db, file, current_user.id, file_type, replace, key
            )
            
            urls.append(db_file.file_url)
            file_ids.append(db_file.id)
        
        return MultipleFileUploadResponse(
            urls=urls,
            file_ids=file_ids,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@file_router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file_by_id(
    file_id: UUID = Path(..., description="The ID of the file to delete"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Delete a file by ID. The file must belong to the current user.
    """
    success = await delete_file(db, file_id, current_user.id)
    if success:
        return FileDeleteResponse(status="deleted")
    else:
        raise HTTPException(status_code=404, detail="File not found")


@file_router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: UUID = Path(..., description="The ID of the file to retrieve"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get file details by ID. The file must belong to the current user.
    """
    file = await get_file(db, file_id, current_user.id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@file_router.put("/{file_id}", response_model=FileResponse)
async def update_file_by_id(
    file_update: FileUpdate,
    file_id: UUID = Path(..., description="The ID of the file to update"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Update file details by ID. Currently only supports renaming the file.
    The file must belong to the current user.
    """
    updated_file = await update_file(db, file_id, current_user.id, file_update)
    if not updated_file:
        raise HTTPException(status_code=404, detail="File not found")
    return updated_file


@file_router.get("/", response_model=FileList)
async def list_files(
    skip: int = Query(0, ge=0, description="Number of files to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of files to return"),
    file_type: Optional[FileType] = Query(None, description="Filter files by type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    List all files belonging to the current user with pagination and optional filtering.
    """
    files, count = await get_files(db, current_user.id, skip, limit, file_type)
    return FileList(items=[FileResponse.model_validate(file) for file in files], count=count)


@file_router.get("/storage/info", response_model=StorageResponse)
async def get_storage_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
    create_if_missing: bool = Query(True, description="Create storage info if missing")
):
    """
    Get storage information for the current user.
    """
    storage = await get_user_storage(db, current_user.id)
    if not storage:
        if create_if_missing:
            storage_data = StorageCreate(
                total_space=10737418240,  # Default 10GB
                used_space=0,
                user_id=current_user.id,
            )
            storage = await create_storage(db, storage_data)
            if not storage:
                raise HTTPException(
                    status_code=500,
                    detail="Error creating storage information"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail="Storage information not found"
            )

    return storage



@file_router.put('/storage/extend', response_model=StorageResponse)
async def extend_storage(
    storage_update: StorageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Extend storage for the current user.
    """
    storage = await update_storage(db, current_user.id, storage_update)
    if not storage:
        raise HTTPException(status_code=404, detail="Storage information not found")
    return storage


# Analytics Routes
@file_router.get("/analytics/type-distribution", response_model=FileTypeDistribution)
async def get_file_type_distribution_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get the distribution of file types for the current user.
    Returns counts for each file type.
    """
    distribution = await get_file_type_distribution(db, current_user.id)
    return {"type_distribution": distribution}


@file_router.get("/analytics/storage-trends", response_model=StorageUsageTrend)
async def get_storage_usage_trends_route(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get storage usage trends over time for the current user.
    Returns daily snapshots of total files and total size.
    """    
    trends = await get_storage_usage_trends(db, current_user.id, days=days)
    return {"storage_trends": trends}


@file_router.get("/analytics/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity_route(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of activities to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get recent file activity for the current user.
    Returns a list of recently uploaded or updated files.
    """    
    activity = await get_recent_activity(db, current_user.id, limit=limit)
    return {"recent_activity": activity}


@file_router.get("/analytics/large-files", response_model=LargeFilesResponse)
async def get_large_files_route(
    min_size_mb: int = Query(10, ge=1, description="Minimum file size in MB"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of files to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get the largest files for the current user.
    Returns a list of files larger than min_size_mb, ordered by size (largest first).
    """    
    large_files = await get_large_files(db, current_user.id, min_size_mb=min_size_mb, limit=limit)
    return {"large_files": large_files}


@file_router.get("/analytics/dashboard", response_model=FileAnalyticsDashboard)
async def get_analytics_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back for trends"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get a comprehensive analytics dashboard for the current user.
    Combines multiple analytics endpoints into a single response.
    """
    
    # Gather all analytics in parallel
    type_distribution = await get_file_type_distribution(db, current_user.id)
    storage_trends = await get_storage_usage_trends(db, current_user.id, days=days)
    recent_activity = await get_recent_activity(db, current_user.id, limit=5)
    large_files = await get_large_files(db, current_user.id, min_size_mb=10, limit=5)
    
    # Return comprehensive dashboard
    return {
        "type_distribution": type_distribution,
        "storage_trends": storage_trends,
        "recent_activity": recent_activity,
        "large_files": large_files
    }


# =====================================
# 🔹 File Activity Routes
# =====================================

@file_router.post("/activities", response_model=FileActivityResponse)
async def create_activity(
    activity_data: FileActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Create a new file activity record.
    This can be used by the frontend to manually track specific file actions.
    """
    # Verify that the file belongs to the current user
    file = await get_file(db, activity_data.file_id, current_user.id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        activity = await create_file_activity(db, activity_data)
        return FileActivityResponse(
            id=activity.id,
            file_id=activity.file_id,
            action=activity.action,
            timestamp=activity.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@file_router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Delete a file activity record.
    Only the owner of the associated file can delete the activity.
    """
    success = await delete_file_activity(db, activity_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Activity not found or access denied")
    
    return {"status": "deleted", "message": "Activity deleted successfully"}


@file_router.get("/activities", response_model=RecentActivityResponse)
async def get_activities(
    limit: int = Query(50, ge=1, le=100, description="Number of activities to retrieve"),
    skip: int = Query(0, ge=0, description="Number of activities to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """
    Get file activities for the current user with pagination.
    Returns activities with file details sorted by most recent first.
    """
    activities = await get_user_file_activities(db, current_user.id, limit=limit, skip=skip)
    
    return RecentActivityResponse(recent_activity=activities)