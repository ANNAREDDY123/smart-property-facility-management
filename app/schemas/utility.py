from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


UTILITY_TYPES = {
    "Electricity",
    "Water",
    "Gas",
    "Internet",
}


UTILITY_STATUSES = {
    "Pending",
    "Paid",
    "Cancelled",
}


class UtilityReadingCreate(BaseModel):
    unit_id: int = Field(gt=0)

    utility_type: str = Field(
        min_length=1,
        max_length=30,
    )

    previous_reading: float = Field(
        ge=0,
    )

    current_reading: float = Field(
        ge=0,
    )

    rate: float = Field(
        gt=0,
    )

    billing_month: str = Field(
        min_length=7,
        max_length=7,
    )

    @field_validator("utility_type")
    @classmethod
    def validate_utility_type(cls, value: str):
        if value not in UTILITY_TYPES:
            raise ValueError("Invalid utility type")

        return value

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


class UtilityReadingResponse(BaseModel):
    id: int
    unit_id: int
    utility_type: str
    previous_reading: float
    current_reading: float
    units_consumed: float
    rate: float
    total_amount: float
    billing_month: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class UtilityInvoiceCreate(BaseModel):
    unit_id: int = Field(gt=0)

    utility_type: str = Field(
        min_length=1,
        max_length=30,
    )

    billing_month: str = Field(
        min_length=7,
        max_length=7,
    )

    units_consumed: float = Field(
        ge=0,
    )

    rate: float = Field(
        gt=0,
    )

    status: str = "Pending"

    @field_validator("utility_type")
    @classmethod
    def validate_utility_type(cls, value: str):
        if value not in UTILITY_TYPES:
            raise ValueError("Invalid utility type")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        if value not in UTILITY_STATUSES:
            raise ValueError("Invalid utility invoice status")

        return value

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


class UtilityInvoiceResponse(BaseModel):
    id: int
    unit_id: int
    utility_type: str
    billing_month: str
    units_consumed: float
    rate: float
    total_amount: float
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )