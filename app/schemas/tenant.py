from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=150)
    phone: str = Field(min_length=7, max_length=20)
    identification_number: str = Field(
        min_length=2,
        max_length=100,
    )
    emergency_contact: str = Field(
        min_length=2,
        max_length=150,
    )
    address: str = Field(
        min_length=2,
        max_length=255,
    )


class TenantUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=150,
    )
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
    )
    identification_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    emergency_contact: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    address: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )


class TenantResponse(TenantCreate):
    id: int

    model_config = {
        "from_attributes": True,
    }