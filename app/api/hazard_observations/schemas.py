from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.api.hazard_observations.models import (
    ControlMeasureEnum,
    HazardObservation,
    HazardTypeEnum,
    ObservationStatus,
    PotentialRiskEnum,
    UnsafeReasonEnum,
)
from app.core.schema_operations import BaseModel


class HazardObservationSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # Photo File IDs
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Photo file IDs")

    # Observer Information
    observer_id: UUID = Field(..., description="ID of the person who observed the hazard")
    observer_name: Optional[str] = Field(None, description="Name of the observer")
    facility_id: UUID = Field(..., description="Facility where hazard was observed")
    facility_name: Optional[str] = Field(None, description="Facility name")

    # Observation Date/Time
    observation_date: date = Field(..., description="Date of observation")
    observation_time: time = Field(..., description="Time of observation")

    # Unsafe Action/Condition
    unsafe_action_condition: str = Field(
        ..., description="Description of unsafe action or condition observed"
    )

    # Hazard Types (can select multiple)
    hazard_types: Optional[List[str]] = Field(
        None, description="Types of hazards identified"
    )

    # Potential Risks (can select multiple)
    potential_risks: Optional[List[str]] = Field(
        None, description="Potential risks from the hazard"
    )
    potential_risk_other: Optional[str] = Field(
        None, description="Other potential risk details"
    )

    # Why Unsafe (can select multiple)
    unsafe_reasons: Optional[List[str]] = Field(
        None, description="Reasons why the work was done unsafely"
    )
    unsafe_reason_other: Optional[str] = Field(
        None, description="Other unsafe reason details"
    )

    # Control Measures (can select multiple)
    control_measures: Optional[List[str]] = Field(
        None, description="Control measures taken or recommended"
    )
    control_measure_other: Optional[str] = Field(
        None, description="Other control measure details"
    )

    # Corrective Action
    corrective_action: Optional[str] = Field(
        None, description="Corrective action taken or suggested"
    )

    # Status
    status: ObservationStatus = Field(
        default=ObservationStatus.OPEN, description="Current status of the observation"
    )

    # Resolution Information
    resolved_by_id: Optional[UUID] = Field(
        None, description="ID of HSE employee who resolved the hazard"
    )
    resolved_by_name: Optional[str] = Field(None, description="Name of the resolver")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes from HSE")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    class Meta:
        orm_model = HazardObservation


class HazardObservationCreateSchema(BaseModel):
    # Observer will be set from current user, so not included here
    facility_id: UUID = Field(..., description="Facility where hazard was observed")

    # Observation Date/Time
    observation_date: date = Field(..., description="Date of observation")
    observation_time: time = Field(..., description="Time of observation")

    # Unsafe Action/Condition
    unsafe_action_condition: str = Field(
        ...,
        description="Description of unsafe action or condition observed",
        min_length=10,
    )

    # Hazard Types (can select multiple)
    hazard_types: Optional[List[HazardTypeEnum]] = Field(
        None, description="Types of hazards identified"
    )

    # Potential Risks (can select multiple)
    potential_risks: Optional[List[PotentialRiskEnum]] = Field(
        None, description="Potential risks from the hazard"
    )
    potential_risk_other: Optional[str] = Field(
        None, description="Other potential risk details"
    )

    # Why Unsafe (can select multiple)
    unsafe_reasons: Optional[List[UnsafeReasonEnum]] = Field(
        None, description="Reasons why the work was done unsafely"
    )
    unsafe_reason_other: Optional[str] = Field(
        None, description="Other unsafe reason details"
    )

    # Control Measures (can select multiple)
    control_measures: Optional[List[ControlMeasureEnum]] = Field(
        None, description="Control measures taken or recommended"
    )
    control_measure_other: Optional[str] = Field(
        None, description="Other control measure details"
    )

    # Corrective Action
    corrective_action: Optional[str] = Field(
        None, description="Corrective action taken or suggested"
    )

    # Photo File IDs
    photo_file_ids: Optional[List[UUID]] = Field(
        None, description="Photo file IDs for uploaded images"
    )


class HazardObservationUpdateSchema(BaseModel):
    facility_id: Optional[UUID] = Field(None, description="Facility where hazard was observed")
    observation_date: Optional[date] = Field(None, description="Date of observation")
    observation_time: Optional[time] = Field(None, description="Time of observation")
    unsafe_action_condition: Optional[str] = Field(
        None, description="Description of unsafe action or condition observed"
    )
    hazard_types: Optional[List[HazardTypeEnum]] = Field(
        None, description="Types of hazards identified"
    )
    potential_risks: Optional[List[PotentialRiskEnum]] = Field(
        None, description="Potential risks from the hazard"
    )
    potential_risk_other: Optional[str] = Field(
        None, description="Other potential risk details"
    )
    unsafe_reasons: Optional[List[UnsafeReasonEnum]] = Field(
        None, description="Reasons why the work was done unsafely"
    )
    unsafe_reason_other: Optional[str] = Field(
        None, description="Other unsafe reason details"
    )
    control_measures: Optional[List[ControlMeasureEnum]] = Field(
        None, description="Control measures taken or recommended"
    )
    control_measure_other: Optional[str] = Field(
        None, description="Other control measure details"
    )
    corrective_action: Optional[str] = Field(
        None, description="Corrective action taken or suggested"
    )
    status: Optional[ObservationStatus] = Field(
        None, description="Current status of the observation"
    )
    photo_file_ids: Optional[List[UUID]] = Field(
        None, description="Photo file IDs for uploaded images"
    )


class HazardObservationResolveSchema(BaseModel):
    resolution_notes: str = Field(
        ..., description="Resolution notes from HSE employee", min_length=10
    )
