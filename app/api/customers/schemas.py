
from datetime import date

from app.api.customers.models import Customer
from app.core.schema_operations import BaseModel


class CustomerSchema(BaseModel):
    full_name: str
    phone_number: str
    email: str
    gender: str
    date_of_birth: date
    notes: str
    is_vip: bool
    is_active: bool

    class Meta:
        orm_model = Customer


