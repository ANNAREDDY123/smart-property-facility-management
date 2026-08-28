from datetime import date

from pydantic import BaseModel, Field, model_validator


class LeaseCreate(BaseModel):
    tenant_id: int = Field(gt=0)
    unit_id: int = Field(gt=0)
    start_date: date
    end_date: date
    monthly_rent: float = Field(gt=0)
    security_deposit: float = Field(gt=0)
    lease_status: str = "Draft"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        return self


class LeaseUpdateStatus(BaseModel):
    lease_status: str


class LeaseResponse(LeaseCreate):
    id: int

    model_config = {
        "from_attributes": True,
    }