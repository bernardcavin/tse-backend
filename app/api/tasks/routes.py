from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution, require_manager
from app.api.auth.utils import get_current_user
from app.api.tasks import crud, schemas
from app.api.tasks.models import Task, TaskStatus
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/tasks")


@router.get(
    "",
    summary="Get All Tasks",
    tags=["Tasks"],
)
async def get_all_tasks(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Pass user info if we decided to filter, for now passing request
    tasks = crud.get_all_tasks(db, request)
    return create_api_response(
        success=True, message="Tasks retrieved successfully", data=tasks
    )


@router.post(
    "",
    summary="Create Task",
    tags=["Tasks"],
)
async def create_task(
    task: schemas.TaskSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_task(db, task, user.id)
    log_contribution(db, user, "CREATED", "tasks", task.title)
    return create_api_response(success=True, message="Task created successfully")


@router.get(
    "/{id}",
    summary="Get Task",
    tags=["Tasks"],
)
async def get_task(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    task = crud.get_task(db, id)
    return create_api_response(
        success=True, message="Task retrieved successfully", data=task
    )


@router.put(
    "/{id}",
    summary="Update Task",
    tags=["Tasks"],
)
async def update_task(
    id: UUID,
    task: schemas.TaskSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Check permissions
    # "employees cannot delete tasks and once finished cannot be edited, only managers have full control."
    
    current_task = crud.get_task(db, id)
    
    if user.role != "MANAGER":
        # Check if finished
        if current_task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees cannot edit finished tasks",
            )
            
    crud.update_task(db, id, task)
    log_contribution(db, user, "UPDATED", "tasks", task.title)
    return create_api_response(success=True, message="Task updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Task (Manager Only)",
    tags=["Tasks"],
)
async def delete_task(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Verify user is manager
    require_manager(user)

    crud.delete_task(db, id)
    log_contribution(db, user, "DELETED", "tasks", f"id={id}")
    return create_api_response(success=True, message="Task deleted successfully")
