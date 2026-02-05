import enum
import uuid
from datetime import date, datetime, time

from app.core.database import Base
from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship


class ObservationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ObservationTypeEnum(str, enum.Enum):
    SAFE_ACT = "safe_act"  # Tindakan Aman
    UNSAFE_ACT = "unsafe_act"  # Tindakan Tidak Aman
    SAFE_CONDITION = "safe_condition"  # Kondisi Aman
    UNSAFE_CONDITION = "unsafe_condition"  # Kondisi Tidak Aman
    NEAR_MISS = "near_miss"  # Near Miss / Hampir Celaka
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"  # Usulan Perbaikan


class ObservationCategoryEnum(str, enum.Enum):
    WORKER_BEHAVIOR = "worker_behavior"  # Perilaku / Tindakan Pekerja
    EQUIPMENT_MACHINERY = "equipment_machinery"  # Peralatan / Mesin
    WORK_ENVIRONMENT = "work_environment"  # Lingkungan Kerja
    PROCEDURE_WORK_METHOD = "procedure_work_method"  # Prosedur / Metode Kerja
    PPE = "ppe"  # APD (Alat Pelindung Diri)
    HOUSEKEEPING = "housekeeping"  # Housekeeping
    OTHER = "other"  # Lainnya


class PotentialImpactEnum(str, enum.Enum):
    MINOR_INJURY = "minor_injury"  # Cedera Ringan
    SERIOUS_INJURY = "serious_injury"  # Cedera Berat
    EQUIPMENT_DAMAGE = "equipment_damage"  # Kerusakan Alat
    ENVIRONMENTAL_DAMAGE = "environmental_damage"  # Kerusakan Lingkungan
    FATALITY = "fatality"  # Fatality
    NO_IMPACT = "no_impact"  # Tidak Ada Dampak


class SafetyObservation(Base):
    __tablename__ = "safety_observations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 A. General Information (Informasi Umum)
    observation_date = Column(Date, nullable=False)
    observation_time = Column(Time, nullable=False)
    location_area = Column(String, nullable=True)  # Lokasi/Area Kerja
    department_unit = Column(String, nullable=True)  # Departemen/Unit
    facility_id = Column(PG_UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=True)  # Optional facility

    # 🔹 B. Reporter Data (Data Pelapor)
    observer_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 🔹 C. Observation Type (Jenis Observasi) - can select multiple
    observation_types = Column(ARRAY(String), nullable=True)

    # 🔹 D. Observation Category (Kategori Observasi) - can select multiple
    observation_categories = Column(ARRAY(String), nullable=True)
    category_other = Column(Text, nullable=True)  # For "Lainnya" details

    # 🔹 E. Observation Description (Deskripsi Observasi)
    observation_description = Column(Text, nullable=False)

    # 🔹 F. Potential Risk/Impact (Potensi Risiko / Dampak) - can select multiple
    potential_impacts = Column(ARRAY(String), nullable=True)
    impact_explanation = Column(Text, nullable=True)  # Penjelasan singkat

    # 🔹 G. Suggested Corrective Action (Tindakan Perbaikan yang Disarankan)
    suggested_corrective_action = Column(Text, nullable=True)

    # 🔹 H. Immediate Action (Tindakan Langsung)
    immediate_action_done = Column(String, nullable=True)  # "sudah_dilakukan" or "belum_dilakukan"
    immediate_action_description = Column(Text, nullable=True)  # Jika sudah, jelaskan

    # 🔹 I. Supporting Evidence (Foto / Bukti Pendukung)
    photo_file_ids = Column(ARRAY(PG_UUID), nullable=True)
    has_supporting_evidence = Column(String, nullable=True)  # "terlampir" or "tidak_ada"

    # 🔹 Status
    status = Column(
        Enum(ObservationStatus),
        nullable=False,
        default=ObservationStatus.OPEN,
    )

    # 🔹 Resolution Information (HSE Only)
    resolved_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # 🔹 Close Information (HSE/Manager can close invalid observations)
    closed_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime, nullable=True)
    close_reason = Column(Text, nullable=True)

    # 🔹 Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 🔹 Relationships
    observer = relationship("User", foreign_keys=[observer_id])
    facility = relationship("Facility", foreign_keys=[facility_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    closed_by = relationship("User", foreign_keys=[closed_by_id])

