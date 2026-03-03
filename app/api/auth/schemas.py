from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import model_validator
from app.core.schema_operations import BaseModel


class EnrollFaceRequest(BaseModel):
    face_embedding: list[float]  # pre-computed embedding from client-side TFLite


class UserSchema(BaseModel):
    id: UUID
    name: str
    username: str
    employee_num: Optional[str] = None
    email: Optional[str] = None
    nik: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None
    hire_date: Optional[datetime] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    role: str
    attachment_file_ids: Optional[list[UUID]] = None
    face_embedding: Optional[list[float]] = None
    has_face_embedding: bool = False

    @model_validator(mode="before")
    @classmethod
    def set_has_face_embedding(cls, data):
        if isinstance(data, dict):
            # Incoming data might be a dict (e.g., from an API payload)
            # Actually we usually create schemas from SQLAlchemy models via model_validate()
            # In that case, mode='before' gets the SQLAlchemy object. Let's use mode='after' instead or check getattr.
            if "face_embedding" in data:
                data["has_face_embedding"] = data["face_embedding"] is not None
            elif hasattr(data, "face_embedding"):
                data["has_face_embedding"] = getattr(data, "face_embedding") is not None
        else:
            # It's an ORM instance
            data.has_face_embedding = getattr(data, "face_embedding", None) is not None
        return data


# Define a Pydantic model for the JSON payload
class TokenRequest(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    token_type: str
    access_token: str


# Employee Management Schemas
class CreateEmployeeSchema(BaseModel):
    username: str
    name: str
    employee_num: Optional[str] = None
    email: Optional[str] = None
    nik: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None
    hire_date: Optional[datetime] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    password: str
    role: str = "EMPLOYEE"  # Default to EMPLOYEE
    attachment_file_ids: list[UUID] = []


class UpdateEmployeeSchema(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    employee_num: Optional[str] = None
    email: Optional[str] = None
    nik: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    phone_number: Optional[str] = None
    hire_date: Optional[datetime] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    attachment_file_ids: Optional[list[UUID]] = None


# Profile Update Schema (personal data only, no employment info)
class UpdateProfileSchema(BaseModel):
    username: Optional[str] = None
    name: Optional[str] = None
    nik: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    password: Optional[str] = None

