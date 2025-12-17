import enum
import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    MANAGER = "MANAGER"
    EMPLOYEE = "EMPLOYEE"


class DepartmentEnum(str, enum.Enum):
    HSE = "HSE"
    FINANCE = "Finance"
    OPERATION = "Operation"
    IT = "IT"
    ENGINEERING = "Engineering"
    PROCUREMENT = "Procurement"
    HR = "HR"
    MAINTENANCE = "Maintenance"
    QA_QC = "QA/QC"
    SAFETY = "Safety"
    OTHER = "Other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(), primary_key=True, default=lambda: uuid.uuid4(), nullable=False
    )
    username: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(50))
    employee_num: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    nik: Mapped[str] = mapped_column(String(50), nullable=True)
    position: Mapped[str] = mapped_column(String(100), nullable=True)
    department: Mapped[DepartmentEnum] = mapped_column(
        Enum(DepartmentEnum), nullable=True
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    hire_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    emergency_contact_name: Mapped[str] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(String(128))

    created_at: Mapped[DateTime] = mapped_column(DateTime)
    updated_at: Mapped[DateTime] = mapped_column(DateTime)

    actions = relationship(
        "UserLog", back_populates="user", foreign_keys="UserLog.user_id"
    )
    contributions = relationship(
        "UserAction", back_populates="user", foreign_keys="UserAction.user_id"
    )


class UserLog(Base):
    __tablename__ = "user_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(column="users.id"), nullable=True)
    path = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(String, nullable=False)
    request_body = Column(JSON, nullable=True)
    response_body = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="actions", foreign_keys=[user_id])


class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(column="users.id"),
        nullable=False,
    )

    action = Column(String, nullable=False)  # e.g. "CREATED", "EDITED", "DELETED"
    entity = Column(String, nullable=False)  # e.g. "Well Plan", "Report", "User"
    entity_name = Column(String, nullable=True)  # e.g. "Alpha-1", "Monthly Report Sept"

    description = Column(String, nullable=True)  # full human-readable text
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="contributions", foreign_keys=[user_id])

    def __repr__(self):
        return f"<UserAction {self.description} at {self.timestamp:%Y-%m-%d %H:%M:%S}>"
