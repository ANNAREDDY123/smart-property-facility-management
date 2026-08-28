from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.payment import Payment
from app.models.rent_invoice import RentInvoice
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


PAYMENT_STATUSES = {
    "Pending",
    "Success",
    "Failed",
    "Refunded",
}


@router.post(
    "",
    response_model=PaymentResponse,
)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    invoice = db.query(RentInvoice).filter(
        RentInvoice.id == payment_data.invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Rent invoice not found",
        )

    if payment_data.payment_status not in PAYMENT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status",
        )

    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than 0",
        )

    if invoice.status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cannot pay a cancelled invoice",
        )

    existing_payment = db.query(Payment).filter(
        Payment.transaction_reference
        == payment_data.transaction_reference
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="Transaction reference already exists",
        )

    paid_amounts = db.query(Payment).filter(
        Payment.invoice_id == invoice.id,
        Payment.payment_status == "Success",
    ).with_entities(
        Payment.amount
    ).all()

    total_paid = sum(
        payment.amount
        for payment in paid_amounts
    )

    remaining_amount = (
        invoice.total_amount - total_paid
    )

    if remaining_amount <= 0:
        raise HTTPException(
            status_code=409,
            detail="Invoice is already fully paid",
        )

    if payment_data.amount > remaining_amount:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds invoice balance",
        )

    payment = Payment(
        invoice_id=payment_data.invoice_id,
        amount=payment_data.amount,
        payment_method=payment_data.payment_method,
        payment_status=payment_data.payment_status,
        transaction_reference=payment_data.transaction_reference,
    )

    db.add(payment)

    try:
        db.flush()

        if payment_data.payment_status == "Success":
            new_total_paid = (
                total_paid + payment_data.amount
            )

            if new_total_paid >= invoice.total_amount:
                invoice.status = "Paid"

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Transaction reference already exists",
        )

    db.refresh(payment)

    # Create audit log after successful payment creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Payment",
        entity_id=payment.id,
        description=(
            f"Payment #{payment.id} created for "
            f"invoice #{payment.invoice_id}. "
            f"Amount: {payment.amount:.2f}, "
            f"status: {payment.payment_status}."
        ),
    )

    return payment


@router.get(
    "",
    response_model=list[PaymentResponse],
)
def get_payments(
    invoice_id: int | None = None,
    payment_status: str | None = None,
    billing_month: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="id",
        pattern=(
            "^(id|amount|payment_status|paid_at)$"
        ),
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Payment)
        .join(
            RentInvoice,
            RentInvoice.id == Payment.invoice_id,
        )
    )

    if invoice_id is not None:
        query = query.filter(
            Payment.invoice_id == invoice_id
        )

    if payment_status is not None:
        if payment_status not in PAYMENT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid payment status",
            )

        query = query.filter(
            Payment.payment_status == payment_status
        )

    if billing_month is not None:
        query = query.filter(
            RentInvoice.billing_month == billing_month
        )

    if start_date is not None:
        query = query.filter(
            Payment.paid_at >= start_date
        )

    if end_date is not None:
        if start_date is not None and end_date < start_date:
            raise HTTPException(
                status_code=400,
                detail="end_date cannot be before start_date",
            )

        query = query.filter(
            Payment.paid_at <= end_date
        )

    sort_column = getattr(
        Payment,
        sort_by,
    )

    if sort_order == "desc":
        query = query.order_by(
            sort_column.desc()
        )
    else:
        query = query.order_by(
            sort_column.asc()
        )

    offset = (page - 1) * limit

    return (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment