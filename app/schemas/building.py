from pydantic import BaseModel, Field


class BuildingCreate(BaseModel):
    property_id: int = Field(gt=0)
    building_name: str = Field(min_length=2, max_length=150)
    number_of_floors: int = Field(gt=0)
    total_units: int = Field(gt=0)


class BuildingResponse(BuildingCreate):
    id: int

    model_config = {
        "from_attributes": True,
    }