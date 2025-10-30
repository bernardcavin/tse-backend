import datetime
import os
import uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.files.models import FileRecord, FileRecordStatus
from app.api.files.schemas import FileRecordSchema
from app.core.config import settings

UPLOAD_DIR = settings.LOCAL_UPLOAD_DIR  # e.g., "./uploads"


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(file: UploadFile, db: Session, user):
    ensure_upload_dir()
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]  # type: ignore
    local_filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, local_filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    file_size = os.path.getsize(file_path)

    uploaded_file = FileRecord(
        id=file_id,
        filename=file.filename,
        size=file_size,
        content_type=file.content_type or "unknown",
        upload_date=datetime.datetime.now(datetime.timezone.utc),
        status=FileRecordStatus.UPLOADED,
        uploaded_by_id=user.id,
    )

    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)

    return uploaded_file


def get_file_path(file_id: UUID, db: Session):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(UPLOAD_DIR, uploaded_file.key)  # type: ignore
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on disk")

    return file_path


def get_file_metadata(file_id: UUID, db: Session):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    return FileRecordSchema.model_validate(uploaded_file)


def update_file_metadata(file_id: UUID, db: Session):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File metadata not found")

    file_path = os.path.join(UPLOAD_DIR, uploaded_file.key)  # type: ignore
    if os.path.exists(file_path):
        uploaded_file.size = os.path.getsize(file_path)  # type: ignore
        uploaded_file.status = FileRecordStatus.UPLOADED  # type: ignore
    else:
        uploaded_file.status = FileRecordStatus.MISSING  # type: ignore

    db.commit()


def get_image_url(file_id: UUID, db: Session):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(UPLOAD_DIR, uploaded_file.key)  # type: ignore
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Optionally resize or transform here if needed (e.g., using Pillow)
    # For now, just return local static path
    return f"/static/uploads/{uploaded_file.key}"
