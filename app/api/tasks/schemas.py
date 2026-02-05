from datetime import datetime, date as date_type
from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.api.tasks.models import Task, TaskStatus, TaskPriority
from app.core.schema_operations import BaseModel
from app.api.auth.schemas import UserSchema


class TaskSchema(BaseModel):
    id: Optional[UUID] = None
    
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description")
    
    status: TaskStatus = Field(TaskStatus.PLANNED, description="Current status of the task")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Priority level")
    
    date: date_type = Field(..., description="Date of the task")
    time_start: Optional[str] = Field(None, description="Start time (HH:MM)")
    time_end: Optional[str] = Field(None, description="End time (HH:MM)")
    
    start_date: Optional[datetime] = Field(None, description="Planned start date")
    end_date: Optional[datetime] = Field(None, description="Planned end date")
    
    created_by_id: Optional[UUID] = Field(None, description="ID of the creator (auto-filled)")
    created_by: Optional[UserSchema] = Field(None, description="Creator details")
    
    assignee_ids: List[UUID] = Field([], description="List of assigned employee IDs")
    attachment_file_ids: List[UUID] = Field([], description="List of attachment file IDs")
    
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Meta:
        orm_model = Task
