from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unit import Unit
from app.models.user import User
from app.models.utility_invoice import UtilityInvoice
from app.models.utility_reading import UtilityReading
from app.schemas.utility import (
    UtilityInvoiceCreate,
    UtilityInvoiceResponse,
    UtilityReadingCreate,
    UtilityReadingResponse,
    UTILITY_STATUSES,
    UTILITY_TYPES,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/utilities",
    tags=["Utilities"],
)


def get_unit_or_404(
    db: Session,
    unit_id: int,
):
    unit = db.query(Unit).filter(
        Unit.id == unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found",
        )

    return unit


def validate_utility_type(
    utility_type: str,
):
    if utility_type not in UTILITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid utility type",
        )


def validate_status(
    status: str,
):
    if status not in UTILITY_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid utility invoice status",
        )


@router.post(
    "/readings",
    response_model=UtilityReadingResponse,
)
def create_utility_reading(
    reading_data: UtilityReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
        )
    ),
):
    get_unit_or_404(
        db=db,
        unit_id=reading_data.unit_id,
    )

    validate_utility_type(
        reading_data.utility_type
    )

    if (
        reading_data.current_reading
        < reading_data.previous_reading
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Current reading cannot be lower "
                "than previous reading"
            ),
        )

    units_consumed = (
        reading_data.current_reading
        - reading_data.previous_reading
    )

    total_amount = (
        units_consumed
        * reading_data.rate
    )

    reading = UtilityReading(
        unit_id=reading_data.unit_id,
        utility_type=reading_data.utility_type,
        previous_reading=reading_data.previous_reading,
        current_reading=reading_data.current_reading,
        units_consumed=units_consumed,
        rate=reading_data.rate,
        total_amount=total_amount,
        billing_month=reading_data.billing_month,
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Create audit log after successful utility reading creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="UtilityReading",
        entity_id=reading.id,
        description=(
            f"Utility reading #{reading.id} created "
            f"for unit #{reading.unit_id}. "
            f"Type: {reading.utility_type}, "
            f"billing month: {reading.billing_month}, "
            f"units consumed: {reading.units_consumed}, "
            f"total amount: {reading.total_amount:.2f}."
        ),
    )

    return reading


@router.get(
    "/readings",
    response_model=list[UtilityReadingResponse],
)
def get_utility_readings(
    unit_id: int | None = None,
    utility_type: str | None = None,
    billing_month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(UtilityReading)

    if unit_id is not None:
        query = query.filter(
            UtilityReading.unit_id == unit_id
        )

    if utility_type is not None:
        validate_utility_type(
            utility_type
        )

        query = query.filter(
            UtilityReading.utility_type
            == utility_type
        )

    if billing_month is not None:
        query = query.filter(
            UtilityReading.billing_month
            == billing_month
        )

    return query.order_by(
        UtilityReading.id
    ).all()


@router.post(
    "/invoices",
    response_model=UtilityInvoiceResponse,
)
def create_utility_invoice(
    invoice_data: UtilityInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
        )
    ),
):
    get_unit_or_404(
        db=db,
        unit_id=invoice_data.unit_id,
    )

    validate_utility_type(
        invoice_data.utility_type
    )

    validate_status(
        invoice_data.status
    )

    total_amount = (
        invoice_data.units_consumed
        * invoice_data.rate
    )

    invoice = UtilityInvoice(
        unit_id=invoice_data.unit_id,
        utility_type=invoice_data.utility_type,
        billing_month=invoice_data.billing_month,
        units_consumed=invoice_data.units_consumed,
        rate=invoice_data.rate,
        total_amount=total_amount,
        status=invoice_data.status,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Create audit log after successful utility invoice creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="UtilityInvoice",
        entity_id=invoice.id,
        description=(
            f"Utility invoice #{invoice.id} created "
            f"for unit #{invoice.unit_id}. "
            f"Type: {invoice.utility_type}, "
            f"billing month: {invoice.billing_month}, "
            f"total amount: {invoice.total_amount:.2f}, "
            f"status: {invoice.status}."
        ),
    )

    return invoice


@router.get(
    "/invoices",
    response_model=list[UtilityInvoiceResponse],
)
def get_utility_invoices(
    unit_id: int | None = None,
    utility_type: str | None = None,
    billing_month: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(UtilityInvoice)

    if unit_id is not None:
        query = query.filter(
            UtilityInvoice.unit_id == unit_id
        )

    if utility_type is not None:
        validate_utility_type(
            utility_type
        )

        query = query.filter(
            UtilityInvoice.utility_type
            == utility_type
        )

    if billing_month is not None:
        query = query.filter(
            UtilityInvoice.billing_month
            == billing_month
        )

    if status is not None:
        validate_status(status)

        query = query.filter(
            UtilityInvoice.status == status
        )

    return query.order_by(
        UtilityInvoice.id
    ).all()