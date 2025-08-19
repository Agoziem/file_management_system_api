from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID
import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, func, extract, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.files.models import File, FileType, Storage
from app.api.v1.files.schemas import FileCreate, FileUpdate, StorageCreate, StorageUpdate
from app.api.v1.files.utils import upload_or_replace_file, delete_file as delete_s3_file

MB = 1024 * 1024  # 1 MB in bytes
DEFAULT_STORAGE_LIMIT = 100 * MB  # 100 MB default storage limit


async def create_file(db: AsyncSession, file_data: FileCreate, user_id: UUID) -> File:
    """Create a new file record in database"""
    
    # Check if user has enough storage space
    storage = await get_user_storage(db, user_id)
    if not storage:
        # Create default storage for user if not exists
        storage_data = StorageCreate(user_id=user_id, total_space=DEFAULT_STORAGE_LIMIT, used_space=0)
        storage = await create_storage(db, storage_data)
    
    # Check if user has enough space
    if storage.used_space + file_data.file_size > storage.total_space:
        raise HTTPException(status_code=413, detail="Not enough storage space")
    
    # Create file
    db_file = File(
        user_id=user_id,
        file_name=file_data.file_name,
        file_type=file_data.file_type,
        file_size=file_data.file_size,
        file_url=file_data.file_url
    )
    
    try:
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        
        # Update storage usage
        storage.used_space += file_data.file_size
        db.add(storage)
        await db.commit()
        
        return db_file
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="File with this name already exists")


async def get_file(db: AsyncSession, file_id: UUID, user_id: UUID) -> Optional[File]:
    """Get a file by ID"""
    query = select(File).where(File.id == file_id, File.user_id == user_id)
    result = await db.execute(query)
    file = result.scalar_one_or_none()
    
    if not file:
        return None
    
    return file


async def get_files(
    db: AsyncSession, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100, 
    file_type: Optional[FileType] = None
) -> Tuple[List[File], int]:
    """Get files with pagination and optional filtering"""
    query = select(File).where(File.user_id == user_id)
    
    if file_type:
        query = query.where(File.file_type == file_type)
    
    # Count total
    count_query = select(File.id).where(File.user_id == user_id)
    if file_type:
        count_query = count_query.where(File.file_type == file_type)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.all())
    
    # Get paginated results
    query = query.order_by(File.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    files = result.scalars().all()
    
    return list(files), total_count


async def update_file(
    db: AsyncSession, file_id: UUID, user_id: UUID, file_data: FileUpdate
) -> Optional[File]:
    """Update file details"""
    query = select(File).where(File.id == file_id, File.user_id == user_id)
    result = await db.execute(query)
    file = result.scalar_one_or_none()
    
    if not file:
        return None
    
    if file_data.file_name:
        file.file_name = file_data.file_name
    
    try:
        db.add(file)
        await db.commit()
        await db.refresh(file)
        return file
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="File with this name already exists")


async def delete_file(db: AsyncSession, file_id: UUID, user_id: UUID) -> bool:
    """Delete a file from database and storage"""
    query = select(File).where(File.id == file_id, File.user_id == user_id)
    result = await db.execute(query)
    file = result.scalar_one_or_none()
    
    if not file:
        return False
    
    # Extract key from URL
    file_url = file.file_url
    parts = file_url.split('/')
    key = parts[-1]
    
    # Delete from S3
    success = await delete_s3_file(key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")
    
    # Get storage to update used space
    storage = await get_user_storage(db, user_id)
    if storage:
        storage.used_space = max(0, storage.used_space - file.file_size)
        db.add(storage)
    
    # Delete from database
    await db.delete(file)
    await db.commit()
    
    return True


async def get_user_storage(db: AsyncSession, user_id: UUID) -> Optional[Storage]:
    """Get user's storage information"""
    query = select(Storage).where(Storage.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_storage(db: AsyncSession, storage_data: StorageCreate) -> Storage:
    """Create a new storage record for a user"""
    db_storage = Storage(
        user_id=storage_data.user_id,
        total_space=storage_data.total_space,
        used_space=storage_data.used_space
    )
    
    db.add(db_storage)
    await db.commit()
    await db.refresh(db_storage)
    
    return db_storage


async def update_storage(
    db: AsyncSession, user_id: UUID, storage_data: StorageUpdate
) -> Optional[Storage]:
    """Update user's storage information"""
    query = select(Storage).where(Storage.user_id == user_id)
    result = await db.execute(query)
    storage = result.scalar_one_or_none()
    
    if not storage:
        return None
    
    if storage_data.total_space is not None:
        storage.total_space = storage_data.total_space
    
    if storage_data.used_space is not None:
        storage.used_space = storage_data.used_space
    
    db.add(storage)
    await db.commit()
    await db.refresh(storage)
    
    return storage


async def get_file_by_name(
    db: AsyncSession, user_id: UUID, file_name: str
) -> Optional[File]:
    """Get a file by name and user ID"""
    query = select(File).where(File.user_id == user_id, File.file_name == file_name)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def upload_and_create_file(
    db: AsyncSession,
    file: UploadFile,
    user_id: UUID,
    file_type: FileType,
    replace: bool = False
) -> File:
    """Upload file to S3 and create database record"""
    # Generate a unique key for the file
    key = f"{user_id}/{uuid.uuid4()}/{file.filename}"
    
    # Upload to S3
    file_url = await upload_or_replace_file(file, key, replace)
    
    # Determine file size - file.size doesn't always work, so read the file
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()  # Get current position (size)
    file.file.seek(0)  # Reset position to beginning

    # Validate file
    if not file.filename or not file.file:
        raise HTTPException(status_code=400, detail="Invalid file")

    # Create file record
    file_data = FileCreate(
        file_name=file.filename,
        file_type=file_type,
        file_size=file_size,
        file_url=file_url
    )
    
    return await create_file(db, file_data, user_id)


def determine_file_type(filename: str) -> FileType:
    """Determine file type from filename"""
    filename = filename.lower()
    
    # Image files
    if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']):
        return FileType.IMAGE
    
    # Document files
    if any(filename.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv']):
        return FileType.DOCUMENT
    
    # Video files
    if any(filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']):
        return FileType.VIDEO
    
    # Audio files
    if any(filename.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac']):
        return FileType.AUDIO
    
    # Default to other
    return FileType.OTHER


# Analytics Services

async def get_file_type_distribution(db: AsyncSession, user_id: UUID) -> Dict[str, int]:
    """
    Get the distribution of file types for a user.
    Returns a dictionary with file types as keys and counts as values.
    """
    query = (
        select(File.file_type, func.count(File.id))
        .where(File.user_id == user_id)
        .group_by(File.file_type)
    )
    result = await db.execute(query)
    distribution = {file_type: count for file_type, count in result.all()}
    
    # Ensure all file types are represented, even if count is 0
    for file_type in FileType:
        if file_type not in distribution:
            distribution[file_type] = 0
            
    return distribution


async def get_storage_usage_trends(
    db: AsyncSession, user_id: UUID, days: int = 30
) -> Dict[str, List]:
    """
    Get storage usage trends over time.
    Returns daily snapshots of total files and total size.
    """
    # Calculate the start date (n days ago)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Query for files created within the time range
    query = (
        select(
            func.date_trunc('day', File.created_at).label('day'),
            func.count(File.id).label('file_count'),
            func.sum(File.file_size).label('total_size')
        )
        .where(File.user_id == user_id)
        .where(File.created_at >= start_date)
        .group_by(func.date_trunc('day', File.created_at))
        .order_by(func.date_trunc('day', File.created_at))
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Prepare the return format
    dates = []
    file_counts = []
    sizes = []
    
    for day, file_count, total_size in rows:
        dates.append(day.strftime('%Y-%m-%d'))
        file_counts.append(file_count)
        sizes.append(total_size if total_size else 0)
    
    return {
        "dates": dates,
        "file_counts": file_counts,
        "sizes": sizes
    }


async def get_recent_activity(
    db: AsyncSession, user_id: UUID, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get recent file activity for a user.
    Returns a list of recently uploaded or updated files.
    """
    # Get recently updated files
    query = (
        select(File)
        .where(File.user_id == user_id)
        .order_by(desc(File.updated_at))
        .limit(limit)
    )
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    # Format the results
    activity = []
    for file in files:
        activity.append({
            "id": file.id,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "updated_at": file.updated_at,
            "created_at": file.created_at,
            # If updated_at and created_at are the same, the file was just uploaded
            "action": "uploaded" if file.updated_at == file.created_at else "updated"
        })
    
    return activity


async def get_large_files(
    db: AsyncSession, user_id: UUID, min_size_mb: int = 10, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get the largest files for a user.
    Returns a list of files larger than min_size_mb, ordered by size (largest first).
    """
    min_size_bytes = min_size_mb * MB
    
    query = (
        select(File)
        .where(File.user_id == user_id)
        .where(File.file_size >= min_size_bytes)
        .order_by(desc(File.file_size))
        .limit(limit)
    )
    
    result = await db.execute(query)
    files = result.scalars().all()
    
    # Format the results
    large_files = []
    for file in files:
        large_files.append({
            "id": file.id,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "size_mb": round(file.file_size / MB, 2),  # Convert to MB for readability
            "created_at": file.created_at
        })
    
    return large_files
