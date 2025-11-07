# from uuid import UUID
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.files import crud
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/files", tags=["Utils"])


@router.get("/upload-url", tags=["File"], summary="Get presigned URL")
async def get_presigned_upload_url(
    filename: str,
    size: int,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    presigned_url, file_id = crud.get_presigned_upload_url(filename, size, db, user)
    return create_api_response(
        success=True,
        message="Presigned URL generated successfully",
        data={"presigned_url": presigned_url, "file_id": file_id},
    )


@router.patch(
    "/{file_id}/update-metadata",
    tags=["File"],
    summary="Update File Metadata After Upload",
)
async def update_file_metadata(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_file_metadata(file_id, db, user)
    log_contribution(db, user, "UPDATED", "file metadata", f"file_id={file_id}")
    return create_api_response(success=True, message="Metadata updated successfully")


@router.get("/{file_id}/metadata", tags=["File"], summary="Get File Metadata")
async def get_file_metadata(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    file_metadata = crud.get_file_metadata(file_id, db, user)
    return create_api_response(
        success=True, message="File metadata retrieved successfully", data=file_metadata
    )


@router.get("/{file_id}/download", tags=["File"], summary="Download File")
async def download_file(
    file_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    download_url = crud.get_presigned_download_url(file_id, db, user)
    return create_api_response(
        success=True, message="File downloaded successfully", data=download_url
    )


@router.get("/{file_id}/image", tags=["File"], summary="Get Image URL")
async def get_image_url(
    file_id: UUID,
    width: int = Query(None, description="Width of the image"),
    height: int = Query(None, description="Height of the image"),
    resize_type: str = Query("fit", description="Resize type"),
    enlarge: bool = Query(True, description="Enlarge image"),
    extension: str = Query("jpg", description="Extension of the image"),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    image_url = crud.get_image_url(
        file_id, db, width, height, resize_type, enlarge, extension
    )
    return create_api_response(
        success=True, message="Image URL retrieved successfully", data=image_url
    )
