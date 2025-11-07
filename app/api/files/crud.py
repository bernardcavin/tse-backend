import datetime
import uuid
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.files.models import FileRecord, FileRecordStatus
from app.api.files.schemas import FileRecordSchema
from app.core.config import settings
from app.core.imgproxy import ImgProxy
from app.core.object_storage import generate_presigned_url


def get_presigned_upload_url(filename: str, size: int, db: Session, user):
    id = str(uuid.uuid4())

    presigned_url = generate_presigned_url(id)

    uploaded_file = FileRecord(
        id=id,
        filename=filename,
        size=size,
        content_type="unknown",
        etag="",
        key=id,
        upload_date=datetime.datetime.now(datetime.timezone.utc),
        status=FileRecordStatus.PENDING,
        uploaded_by_id=user.id,
    )
    db.add(uploaded_file)
    db.commit()

    return presigned_url, uploaded_file.id


def get_presigned_download_url(file_id: UUID, db: Session, user):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")

    return uploaded_file.get_download_url()


def update_file_metadata(file_id: UUID, db: Session, user):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File metadata not found")

    uploaded_file.update_file_metadata()

    db.commit()


def get_file_metadata(file_id: UUID, db: Session, user):
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileRecordSchema.model_validate(uploaded_file)


def get_image_url(
    file_id: UUID, db: Session, width, height, resize_type, enlarge, extension
):
    # Generate presigned URL for MinIO (valid for some time)
    uploaded_file = db.query(FileRecord).filter(FileRecord.id == file_id).first()

    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")

    presigned_url = uploaded_file.get_download_url()

    if not presigned_url:
        raise HTTPException(status_code=404, detail="File not found")

    imgproxy_client = ImgProxy.from_s3(
        bucket=settings.S3_BUCKET_NAME,
        object_key=str(file_id),
        proxy_host=settings.IMAGE_PROXY_URL,
        key=settings.IMGPROXY_KEY,
        salt=settings.IMGPROXY_SALT,
        width=width,
        height=height,
        enlarge=enlarge,
    )

    return imgproxy_client.build_url()
