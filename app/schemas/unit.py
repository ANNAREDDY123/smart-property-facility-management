from typing import Optional

from pydantic import BaseModel, Field


UNIT_STATUSES = {
    "Available",
    "Occupied",
    "Reserved",
    "Maintenance",
}


class UnitCreate(BaseModel):
    building_id: int = Field(gt=0)
    unit_number: str = Field(min_length=1, max_length=50)
    floor_number: int = Field(ge=0)
    unit_type: str = Field(min_length=2, max_length=50)
    area: float = Field(gt=0)
    monthly_rent: float = Field(gt=0)
    status: str = "Available"


class UnitUpdate(BaseModel):
    unit_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    floor_number: Optional[int] = Field(
        default=None,
        ge=0,
    )
    unit_type: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
    )
    area: Optional[float] = Field(
        default=None,
        gt=0,
    )
    monthly_rent: Optional[float] = Field(
        default=None,
        gt=0,
    )
    status: Optional[str] = None


class UnitResponse(UnitCreate):
    id: int

    model_config = {
        "from_attributes": True,
    }