from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.api.auth.schemas import UserSchema
from app.api.tasks.models import Task, TaskPriority, TaskStatus
from app.core.schema_operations import BaseModel
from app.utils.datetime import DateOnly
from pydantic import Field


class TaskSchema(BaseModel):
    id: Optional[UUID] = None
    
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description")
    
    status: TaskStatus = Field(TaskStatus.PLANNED, description="Current status of the task")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    
    start_datetime: datetime = Field(..., description="Start datetime")
    end_datetime: datetime = Field(..., description="End datetime")
    
    created_by_id: Optional[UUID] = Field(None, description="ID of the creator (auto-filled)")
    created_by: Optional[UserSchema] = Field(None, description="Creator details")
    
    assignee_ids: List[UUID] = Field([], description="List of assigned employee IDs")
    attachment_file_ids: List[UUID] = Field([], description="List of attachment file IDs")
    
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Meta:
        orm_model = Task
