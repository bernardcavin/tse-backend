
from app.api.employees.models import Employee
from app.core.schema_operations import BaseModel


class EmployeeSchema(BaseModel):
    full_name: str
    phone_number: str
    email: str
    role: str
    specialization: str
    bio: str
    commission_rate: float
    is_active: bool

    class Meta:
        orm_model = Employee