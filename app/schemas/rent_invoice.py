from datetime import date

from pydantic import BaseModel, Field, field_validator


class RentInvoiceCreate(BaseModel):
    lease_id: int = Field(gt=0)

    billing_month: str = Field(
        min_length=7,
        max_length=7,
    )

    rent_amount: float = Field(gt=0)

    late_fee: float = Field(
        default=0,
        ge=0,
    )

    discount: float = Field(
        default=0,
        ge=0,
    )

    due_date: date

    status: str = "Pending"

    @field_validator("billing_month")
    @classmethod
    def validate_billing_month(cls, value: str):
        if len(value) != 7 or value[4] != "-":
            raise ValueError(
                "billing_month must be in YYYY-MM format"
            )

        year, month = value.split("-")

        if not year.isdigit() or not month.isdigit():
            raise ValueError(
                "billing_month must be in YYYY-MM format"
            )

        month_number = int(month)

        if month_number < 1 or month_number > 12:
            raise ValueError(
                "billing_month must be in YYYY-MM format"
            )

        return value


class RentInvoiceResponse(BaseModel):
    id: int
    lease_id: int
    billing_month: str
    rent_amount: float
    late_fee: float
    discount: float
    total_amount: float
    due_date: date
    status: str

    model_config = {
        "from_attributes": True,
    }