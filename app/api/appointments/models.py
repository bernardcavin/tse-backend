import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, relationship

from app.core.database import Base

appointment_employees = Table(
    "appointment_employees",
    Base.metadata,
    Column(
        "appointment_id",
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "employee_id",
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)

    appointment_start = Column(DateTime, nullable=False)
    appointment_end = Column(DateTime, nullable=False)

    total_price = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="scheduled")
    notes = Column(Text, nullable=True)
    is_paid = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    employees = relationship(
        "Employee",
        secondary=appointment_employees,
        backref="appointments",
        lazy="joined",
    )

    def __init__(self, **kwargs):
        """
        Custom init to support employee_ids directly.
        If employee_ids provided, store temporarily until added to session.
        """
        employee_ids = kwargs.pop("employee_ids", None)
        super().__init__(**kwargs)
        self._pending_employee_ids = employee_ids or []

    def __repr__(self):
        return f"<Appointment(id='{self.id}', service_id='{self.service_id}', status='{self.status}')>"

    @property
    def employee_ids(self):
        return [str(e.id) for e in self.employees]

    def load_employees(self, session: Session):
        """Attach employees after object is added to a session."""
        if self._pending_employee_ids:
            from app.api.employees.models import Employee

            self.employees = (
                session.query(Employee)
                .filter(Employee.id.in_(self._pending_employee_ids))
                .all()
            )
            self._pending_employee_ids = []  # clear after assignment
