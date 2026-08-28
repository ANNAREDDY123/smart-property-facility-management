from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


VISITOR_STATUSES = {
    "Expected",
    "Checked In",
    "Checked Out",
    "Cancelled",
}


class VisitorCreate(BaseModel):
    visitor_name: str = Field(
        min_length=1,
        max_length=150,
    )

    phone: str = Field(
        min_length=1,
        max_length=30,
    )

    tenant_id: int = Field(gt=0)

    unit_id: int = Field(gt=0)

    purpose: str = Field(
        min_length=1,
        max_length=255,
    )

    entry_time: datetime | None = None

    visitor_status: str = "Expected"

    @field_validator("visitor_status")
    @classmethod
    def validate_status(cls, value: str):
        if value not in VISITOR_STATUSES:
            raise ValueError(
                "Invalid visitor status"
            )

        return value


class VisitorResponse(BaseModel):
    id: int
    visitor_name: str
    phone: str
    tenant_id: int
    unit_id: int
    purpose: str
    entry_time: datetime | None
    exit_time: datetime | None
    visitor_status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )