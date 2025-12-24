from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.contacts.models import Contact
from app.core.schema_operations import BaseModel


class ContactSchema(BaseModel):
    id: Optional[UUID] = Field(
        default=None, description="Unique identifier for the contact"
    )

    # 🔹 Basic Info
    name: str = Field(..., description="Contact's full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    position: Optional[str] = Field(None, description="Job title/position (Jabatan)")

    # 🔹 Organization
    company: Optional[str] = Field(None, description="Company name (Perusahaan)")
    regional: Optional[int] = Field(
        None, description="Regional number (0=none, 1-4=Regional 1-4)"
    )
    zone: Optional[str] = Field(None, description="Zone (Zona)")
    field: Optional[str] = Field(None, description="Field name")

    # 🔹 Additional Info
    address: Optional[str] = Field(None, description="Physical address")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Meta:
        orm_model = Contact
