from pydantic import BaseModel, ConfigDict, Field, field_validator


PARKING_STATUSES = {
    "Available",
    "Assigned",
    "Blocked",
}

VEHICLE_TYPES = {
    "Car",
    "Bike",
    "SUV",
    "Truck",
    "Other",
}


class ParkingCreate(BaseModel):
    property_id: int = Field(gt=0)

    parking_number: str = Field(
        min_length=1,
        max_length=50,
    )

    status: str = "Available"

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        if value not in PARKING_STATUSES:
            raise ValueError("Invalid parking status")

        return value


class ParkingAssign(BaseModel):
    vehicle_number: str = Field(
        min_length=1,
        max_length=30,
    )

    vehicle_type: str = Field(
        min_length=1,
        max_length=30,
    )

    tenant_id: int = Field(gt=0)

    @field_validator("vehicle_type")
    @classmethod
    def validate_vehicle_type(cls, value: str):
        if value not in VEHICLE_TYPES:
            raise ValueError("Invalid vehicle type")

        return value


class ParkingResponse(BaseModel):
    id: int
    property_id: int
    parking_number: str
    vehicle_number: str | None
    vehicle_type: str | None
    tenant_id: int | None
    status: str

    model_config = ConfigDict(
        from_attributes=True,
    )