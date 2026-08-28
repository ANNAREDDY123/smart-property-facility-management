from typing import Optional

from pydantic import BaseModel, Field


PROPERTY_TYPES = {
    "Apartment",
    "Villa",
    "Commercial",
    "Office",
    "Warehouse",
}


class PropertyBase(BaseModel):
    property_name: str = Field(min_length=2, max_length=150)
    property_type: str
    address: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    total_area: float = Field(gt=0)
    total_units: int = Field(gt=0)
    status: str = "Active"


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    property_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    property_type: Optional[str] = None
    address: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )
    city: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    state: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    total_area: Optional[float] = Field(default=None, gt=0)
    total_units: Optional[int] = Field(default=None, gt=0)
    status: Optional[str] = None


class PropertyResponse(PropertyBase):
    id: int

    model_config = {
        "from_attributes": True,
    }