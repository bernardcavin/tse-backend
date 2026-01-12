from datetime import date, datetime, time
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.api.safety_observations.models import (
    SafetyObservation,
    ObservationCategoryEnum,
    ObservationStatus,
    ObservationTypeEnum,
    PotentialImpactEnum,
)
from app.core.schema_operations import BaseModel


class SafetyObservationSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # A. General Information
    observation_date: date = Field(..., description="Date of observation")
    observation_time: time = Field(..., description="Time of observation")
    location_area: Optional[str] = Field(None, description="Location/Area")
    department_unit: Optional[str] = Field(None, description="Department/Unit")
    facility_id: Optional[UUID] = Field(None, description="Facility ID (Optional)")
    facility_name: Optional[str] = Field(None, description="Facility name")

    # B. Reporter Data
    observer_id: UUID = Field(..., description="ID of the person who observed")
    observer_name: Optional[str] = Field(None, description="Name of the observer")

    # C. Observation Type
    observation_types: Optional[List[str]] = Field(
        None, description="Types of observation"
    )

    # D. Observation Category
    observation_categories: Optional[List[str]] = Field(
        None, description="Categories of observation"
    )
    category_other: Optional[str] = Field(None, description="Other category details")

    # E. Observation Description
    observation_description: str = Field(
        ..., description="Description of observation"
    )

    # F. Potential Risk/Impact
    potential_impacts: Optional[List[str]] = Field(
        None, description="Potential impacts"
    )
    impact_explanation: Optional[str] = Field(None, description="Impact explanation")

    # G. Suggested Corrective Action
    suggested_corrective_action: Optional[str] = Field(
        None, description="Suggested corrective action"
    )

    # H. Immediate Action
    immediate_action_done: Optional[str] = Field(
        None, description="Immediate action status"
    )
    immediate_action_description: Optional[str] = Field(
        None, description="Immediate action description"
    )

    # I. Supporting Evidence
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Photo file IDs")
    has_supporting_evidence: Optional[str] = Field(
        None, description="Has supporting evidence status"
    )

    # Status
    status: ObservationStatus = Field(
        default=ObservationStatus.OPEN, description="Current status"
    )

    # Resolution Information
    resolved_by_id: Optional[UUID] = Field(
        None, description="ID of HSE employee who resolved"
    )
    resolved_by_name: Optional[str] = Field(None, description="Name of the resolver")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    # Close Information
    closed_by_id: Optional[UUID] = Field(None, description="ID of user who closed")
    closed_by_name: Optional[str] = Field(None, description="Name of closer")
    closed_at: Optional[datetime] = Field(None, description="Close timestamp")
    close_reason: Optional[str] = Field(None, description="Reason for closing")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    class Meta:
        orm_model = SafetyObservation


class SafetyObservationCreateSchema(BaseModel):
    # A. General Information
    observation_date: date = Field(..., description="Date of observation")
    observation_time: time = Field(..., description="Time of observation")
    location_area: Optional[str] = Field(None, description="Location/Area")
    department_unit: Optional[str] = Field(None, description="Department/Unit")
    facility_id: Optional[UUID] = Field(None, description="Facility ID (Optional)")


    # C. Observation Type
    observation_types: Optional[List[ObservationTypeEnum]] = Field(
        None, description="Types of observation"
    )

    # D. Observation Category
    observation_categories: Optional[List[ObservationCategoryEnum]] = Field(
        None, description="Categories of observation"
    )
    category_other: Optional[str] = Field(None, description="Other category details")

    # E. Observation Description
    observation_description: str = Field(
        ..., description="Description of observation", min_length=10
    )

    # F. Potential Risk/Impact
    potential_impacts: Optional[List[PotentialImpactEnum]] = Field(
        None, description="Potential impacts"
    )
    impact_explanation: Optional[str] = Field(None, description="Impact explanation")

    # G. Suggested Corrective Action
    suggested_corrective_action: Optional[str] = Field(
        None, description="Suggested corrective action"
    )

    # H. Immediate Action
    immediate_action_done: Optional[str] = Field(
        None, description="Immediate action status"
    )
    immediate_action_description: Optional[str] = Field(
        None, description="Immediate action description"
    )

    # I. Supporting Evidence
    photo_file_ids: Optional[List[UUID]] = Field(
        None, description="Photo file IDs"
    )
    has_supporting_evidence: Optional[str] = Field(
        None, description="Has supporting evidence status"
    )


class SafetyObservationUpdateSchema(BaseModel):
    observation_date: Optional[date] = Field(None, description="Date of observation")
    observation_time: Optional[time] = Field(None, description="Time of observation")
    location_area: Optional[str] = Field(None, description="Location/Area")
    department_unit: Optional[str] = Field(None, description="Department/Unit")
    facility_id: Optional[UUID] = Field(None, description="Facility ID")
 
    observation_types: Optional[List[ObservationTypeEnum]] = Field(
        None, description="Types of observation"
    )
    observation_categories: Optional[List[ObservationCategoryEnum]] = Field(
        None, description="Categories of observation"
    )
    category_other: Optional[str] = Field(None, description="Other category details")
    observation_description: Optional[str] = Field(
        None, description="Description of observation"
    )
    potential_impacts: Optional[List[PotentialImpactEnum]] = Field(
        None, description="Potential impacts"
    )
    impact_explanation: Optional[str] = Field(None, description="Impact explanation")
    suggested_corrective_action: Optional[str] = Field(
        None, description="Suggested corrective action"
    )
    immediate_action_done: Optional[str] = Field(
        None, description="Immediate action status"
    )
    immediate_action_description: Optional[str] = Field(
        None, description="Immediate action description"
    )
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Photo file IDs")
    has_supporting_evidence: Optional[str] = Field(
        None, description="Has supporting evidence status"
    )
    status: Optional[ObservationStatus] = Field(None, description="Current status")


class SafetyObservationResolveSchema(BaseModel):
    resolution_notes: str = Field(
        ..., description="Resolution notes from HSE employee", min_length=10
    )


class SafetyObservationCloseSchema(BaseModel):
    close_reason: str = Field(
        ..., description="Reason for closing the observation", min_length=5
    )
