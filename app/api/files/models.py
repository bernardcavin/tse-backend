import uuid
from enum import Enum as PyEnum
from io import BytesIO, StringIO

from sqlalchemy import BigInteger, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.core.object_storage import (
    generate_presigned_url_for_download,
    get_head_object,
    get_object,
)


class FileRecordStatus(PyEnum):
    PENDING = "PENDING"
    UPLOADED = "UPLOADED"


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(
        UUID(), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    filename = Column(String(255))
    size = Column(BigInteger)
    content_type = Column(String(255))
    etag = Column(String(255))
    key = Column(String(255))
    upload_date = Column(DateTime)
    status = Column(Enum(FileRecordStatus))

    uploaded_by_id = Column(UUID(), nullable=True)

    def update_file_metadata(self):
        # Fetch metadata from MinIO using head_object
        response = get_head_object(self.key)

        if response is None:
            raise Exception("Error fetching metadata from MinIO")

        # Update metadata in the database
        self.size = response.size
        self.content_type = response.content_type
        self.etag = response.etag
        self.status = FileRecordStatus.UPLOADED  # type: ignore

    def get_file_stream(self, as_string: bool = False):
        if self.status != FileRecordStatus.UPLOADED:  # type: ignore
            raise Exception("File is not uploaded")

        object = get_object(self.key)
        if object is None:
            raise Exception("File not found")

        if as_string:
            return StringIO(object.data.decode())
        return BytesIO(object.data)

    def get_download_url(self):
        return generate_presigned_url_for_download(self.key, filename=self.filename)
