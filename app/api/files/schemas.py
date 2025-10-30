from datetime import datetime
from uuid import UUID

from app.api.files.models import FileRecordStatus
from app.core.schema_operations import BaseModel


class FileRecordSchema(BaseModel):
    id: UUID
    filename: str
    size: int
    content_type: str
    upload_date: datetime
    status: FileRecordStatus
    uploaded_by_id: UUID
