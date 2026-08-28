from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceRequestCreate(BaseModel):
    unit_id: int = Field(gt=0)
    tenant_id: int | None = Field(default=None, gt=0)

    category: str = Field(
        default="General",
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str = Field(
        min_length=1,
    )

    priority: str = "Medium"

    assigned_staff: int | None = Field(
        default=None,
        gt=0,
    )

    estimated_cost: float = Field(
        default=0,
        ge=0,
    )

    actual_cost: float = Field(
        default=0,
        ge=0,
    )

    status: str = "Open"


class MaintenanceRequestUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    priority: str | None = None

    assigned_staff: int | None = Field(
        default=None,
        gt=0,
    )

    estimated_cost: float | None = Field(
        default=None,
        ge=0,
    )

    actual_cost: float | None = Field(
        default=None,
        ge=0,
    )

    status: str | None = None


class MaintenanceRequestResponse(BaseModel):
    id: int
    unit_id: int
    tenant_id: int | None

    category: str
    title: str
    description: str
    priority: str

    assigned_staff: int | None

    estimated_cost: float
    actual_cost: float

    status: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )