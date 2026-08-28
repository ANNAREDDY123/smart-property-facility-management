from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


FACILITY_TYPES = {
    "Gym",
    "Swimming Pool",
    "Conference Room",
    "Club House",
    "Sports Area",
}

FACILITY_STATUSES = {
    "Active",
    "Inactive",
}

BOOKING_STATUSES = {
    "Confirmed",
    "Cancelled",
}


class FacilityCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    capacity: int = Field(
        gt=0,
    )

    status: str = "Active"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        if value not in FACILITY_TYPES:
            raise ValueError("Invalid facility type")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        if value not in FACILITY_STATUSES:
            raise ValueError("Invalid facility status")
        return value


class FacilityResponse(BaseModel):
    id: int
    name: str
    capacity: int
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class FacilityBookingCreate(BaseModel):
    tenant_id: int = Field(gt=0)
    booking_date: date
    start_time: time
    end_time: time
    status: str = "Confirmed"

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, value: time, info):
        start_time = info.data.get("start_time")

        if start_time is not None and value <= start_time:
            raise ValueError(
                "end_time must be after start_time"
            )

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        if value not in BOOKING_STATUSES:
            raise ValueError("Invalid booking status")
        return value


class FacilityBookingResponse(BaseModel):
    id: int
    facility_id: int
    tenant_id: int
    booking_date: date
    start_time: time
    end_time: time
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )