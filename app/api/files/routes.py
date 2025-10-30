import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.files import crud
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.security import authorize
from app.core.utils.request import get_request

router = APIRouter(prefix="/files", tags=["Utils"])


@router.post("/upload", tags=["File"], summary="Upload File (Local Storage)")
@authorize(role=["operator", "manager", "superuser"])
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    uploaded_file = crud.save_uploaded_file(file, db, user)
    return create_api_response(
        success=True,
        message="File uploaded successfully",
        data={"file_id": uploaded_file.id, "filename": uploaded_file.filename},
    )


@router.patch(
    "/{file_id}/update-metadata",
    tags=["File"],
    summary="Update File Metadata After Upload",
)
@authorize(role=["operator", "manager", "superuser"])
async def update_file_metadata(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_file_metadata(file_id, db)
    log_contribution(db, user, "UPDATED", "file metadata", f"file_id={file_id}")
    return create_api_response(success=True, message="Metadata updated successfully")


@router.get("/{file_id}/metadata", tags=["File"], summary="Get File Metadata")
@authorize(role=["operator", "manager", "superuser"])
async def get_file_metadata(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    file_metadata = crud.get_file_metadata(file_id, db)
    return create_api_response(
        success=True,
        message="File metadata retrieved successfully",
        data=file_metadata,
    )


@router.get("/{file_id}/download", tags=["File"], summary="Download File (Local)")
@authorize(role=["operator", "manager", "superuser"])
async def download_file(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    file_path = crud.get_file_path(file_id, db)

    if not os.path.exists(file_path):
        return create_api_response(success=False, message="File not found", data=None)

    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/{file_id}/image", tags=["File"], summary="Get Image URL (Local)")
@authorize(role=["operator", "manager", "superuser"])
async def get_image_url(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    image_url = crud.get_image_url(file_id, db)
    return create_api_response(
        success=True, message="Image URL retrieved successfully", data=image_url
    )
