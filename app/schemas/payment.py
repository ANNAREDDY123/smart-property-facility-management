from datetime import datetime

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    invoice_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    payment_method: str = Field(min_length=1, max_length=50)
    payment_status: str = "Success"
    transaction_reference: str = Field(
        min_length=1,
        max_length=100,
    )


class PaymentResponse(PaymentCreate):
    id: int
    paid_at: datetime

    model_config = {
        "from_attributes": True,
    }