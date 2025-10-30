from datetime import datetime
from uuid import UUID

from app.api.appointments.models import Appointment
from app.core.schema_operations import BaseModel


class AppointmentSchema(BaseModel):
    customer_id: UUID
    service_id: UUID
    appointment_start: datetime
    appointment_end: datetime
    total_price: float
    status: str
    notes: str
    is_paid: bool
    employee_ids: list[UUID]

    class Meta:
        orm_model = Appointment
