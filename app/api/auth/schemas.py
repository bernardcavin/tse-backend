from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.schema_operations import BaseModel


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

