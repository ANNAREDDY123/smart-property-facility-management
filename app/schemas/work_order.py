from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderCreate(BaseModel):
    maintenance_request_id: int = Field(gt=0)
    assigned_to: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    priority: str = "Medium"
    status: str = "Pending"
    scheduled_date: datetime | None = None


class WorkOrderUpdate(BaseModel):
    assigned_to: int | None = Field(default=None, gt=0)
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
    )
    priority: str | None = None
    status: str | None = None
    scheduled_date: datetime | None = None
    completed_at: datetime | None = None


class WorkOrderResponse(BaseModel):
    id: int
    maintenance_request_id: int
    assigned_to: int | None
    title: str
    description: str
    priority: str
    status: str
    scheduled_date: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )