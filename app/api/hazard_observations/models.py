import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import ARRAY, Column, DateTime, Enum, ForeignKey, String, Text, Date, Time
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ObservationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class HazardTypeEnum(str, enum.Enum):
    PHYSICAL = "physical"  # Fisik (Kebisingan, Radiasi, Terkena Suhu yang Ekstrim)
    CHEMICAL = "chemical"  # Kimia (Mudah Terbakar, Meledak, Korosi, Reaktif, Kecucuan)
    BIOLOGICAL = "biological"  # Biologi (Virus, Bakteri, Jamur, Hewan)
    ERGONOMIC = "ergonomic"  # Ergonomi (Desain Kerja, Layout Maupun Aktivitas yang Buruk)
    PSYCHOSOCIAL = "psychosocial"  # Psikososial (Stress, Jam Kerja yang Panjang)


class PotentialRiskEnum(str, enum.Enum):
    HIT_BY_OBJECT = "hit_by_object"  # Menabrak/Ditabrak Sesuatu
    SLIP_TRIP_FALL = "slip_trip_fall"  # Terpeleset/Tersandung/Terjatuh
    SHORT_CIRCUIT_BURN = "short_circuit_burn"  # Arus Pendek/Terbakar
    CONTACT_HAZARD = "contact_hazard"  # Kontak Dengan Permukaan Panas/Listrik/Bahan Kimia
    ENVIRONMENTAL_POLLUTION = "environmental_pollution"  # Pencemaran Lingkungan
    OTHER = "other"  # Lain-Lain


class UnsafeReasonEnum(str, enum.Enum):
    INADEQUATE_EQUIPMENT = "inadequate_equipment"  # Peralatan yang Tidak Memadai
    LACK_OF_KNOWLEDGE = "lack_of_knowledge"  # Kurangnya Pengetahuan
    INCORRECT_PPE_USE = "incorrect_ppe_use"  # Penggunaan APD yang Tidak Tepat
    PROCEDURE_VIOLATION = "procedure_violation"  # Melanggar Prosedur
    NO_LOTO_SOCIALIZATION = "no_loto_socialization"  # Tidak ada Sosialisasi Lock Out Tag Out
    OTHER = "other"  # Lain-Lain


class ControlMeasureEnum(str, enum.Enum):
    ELIMINATION = "elimination"  # Eliminasi
    SUBSTITUTION = "substitution"  # Substitusi
    MINIMIZATION = "minimization"  # Minimalisasi
    TRAINING = "training"  # Pelatihan
    PPE = "ppe"  # Alat Pelindung Diri (APD)
    OTHER = "other"  # Lain-Lain


class HazardObservation(Base):
    __tablename__ = "hazard_observations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 Photos
    photo_file_ids = Column(ARRAY(PG_UUID), nullable=True)

    # 🔹 Observer Information (Informasi Pengamat)
    observer_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    facility_id = Column(PG_UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)

    # 🔹 Observation Date/Time (Tanggal/Waktu)
    observation_date = Column(Date, nullable=False)
    observation_time = Column(Time, nullable=False)

    # 🔹 Unsafe Action/Condition (Tindakan/kondisi tidak aman yang diamati)
    unsafe_action_condition = Column(Text, nullable=False)

    # 🔹 Hazard Types (Bahaya) - can select multiple
    hazard_types = Column(ARRAY(String), nullable=True)  # Store enum values

    # 🔹 Potential Risks (Resiko Potensial) - can select multiple
    potential_risks = Column(ARRAY(String), nullable=True)  # Store enum values
    potential_risk_other = Column(Text, nullable=True)  # For "Lain-Lain" details

    # 🔹 Why Unsafe (Mengapa Pekerjaan Ini Dilakukan Tidak Aman) - can select multiple
    unsafe_reasons = Column(ARRAY(String), nullable=True)  # Store enum values
    unsafe_reason_other = Column(Text, nullable=True)  # For "Lain-Lain" details

    # 🔹 Control Measures (Pengendalian yang Dilakukan) - can select multiple
    control_measures = Column(ARRAY(String), nullable=True)  # Store enum values
    control_measure_other = Column(Text, nullable=True)  # For "Lain-Lain" details

    # 🔹 Corrective Action (Tindakan perbaikan yang dilakukan/saran)
    corrective_action = Column(Text, nullable=True)

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

    # 🔹 Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 🔹 Relationships
    observer = relationship("User", foreign_keys=[observer_id])
    facility = relationship("Facility", foreign_keys=[facility_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
