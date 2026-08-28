from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.rent_invoice import RentInvoice
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse
from app.schemas.rent_invoice import (
    RentInvoiceCreate,
    RentInvoiceResponse,
)
from app.services.notifications import (
    notify_rent_due,
    notify_rent_overdue,
)
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/rent",
    tags=["Rent & Payments"],
)


INVOICE_STATUSES = {
    "Pending",
    "Paid",
    "Overdue",
    "Cancelled",
}


PAYMENT_STATUSES = {
    "Pending",
    "Success",
    "Failed",
    "Refunded",
}


def calculate_total_amount(
    rent_amount: float,
    late_fee: float,
    discount: float,
) -> float:
    return (
        rent_amount
        + late_fee
        - discount
    )


def update_overdue_invoices(db: Session) -> None:
    """
    Automatically mark pending invoices as overdue
    when their due date has passed.
    """
    today = date.today()

    overdue_invoices = db.query(
        RentInvoice
    ).filter(
        RentInvoice.status == "Pending",
        RentInvoice.due_date < today,
    ).all()

    if not overdue_invoices:
        return

    for invoice in overdue_invoices:
        invoice.status = "Overdue"

        lease = db.query(Lease).filter(
            Lease.id == invoice.lease_id
        ).first()

        if not lease:
            continue

        tenant = db.query(Tenant).filter(
            Tenant.id == lease.tenant_id
        ).first()

        if not tenant:
            continue

        tenant_user = db.query(User).filter(
            User.email == tenant.email
        ).first()

        if not tenant_user:
            continue

        notify_rent_overdue(
            tenant_user.id,
            invoice.billing_month,
            invoice.total_amount,
        )

    db.commit()


def get_invoice_or_404(
    db: Session,
    invoice_id: int,
) -> RentInvoice:

    invoice = db.query(
        RentInvoice
    ).filter(
        RentInvoice.id == invoice_id
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Rent invoice not found",
        )

    return invoice


@router.post(
    "/invoices/generate",
    response_model=RentInvoiceResponse,
)
def generate_rent_invoice_api(
    invoice_data: RentInvoiceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    lease = db.query(Lease).filter(
        Lease.id == invoice_data.lease_id
    ).first()

    if not lease:
        raise HTTPException(
            status_code=404,
            detail="Lease not found",
        )

    if invoice_data.status not in INVOICE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid invoice status",
        )

    if invoice_data.discount > (
        invoice_data.rent_amount
        + invoice_data.late_fee
    ):
        raise HTTPException(
            status_code=400,
            detail="Discount cannot exceed invoice amount",
        )

    existing_invoice = db.query(
        RentInvoice
    ).filter(
        RentInvoice.lease_id == invoice_data.lease_id,
        RentInvoice.billing_month
        == invoice_data.billing_month,
    ).first()

    if existing_invoice:
        raise HTTPException(
            status_code=409,
            detail=(
                "Rent invoice already exists "
                "for this billing month"
            ),
        )

    total_amount = calculate_total_amount(
        rent_amount=invoice_data.rent_amount,
        late_fee=invoice_data.late_fee,
        discount=invoice_data.discount,
    )

    invoice = RentInvoice(
        lease_id=invoice_data.lease_id,
        billing_month=invoice_data.billing_month,
        rent_amount=invoice_data.rent_amount,
        late_fee=invoice_data.late_fee,
        discount=invoice_data.discount,
        total_amount=total_amount,
        due_date=invoice_data.due_date,
        status=invoice_data.status,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    # Notify the tenant about the new rent invoice.
    if invoice.status == "Pending":
        tenant = db.query(Tenant).filter(
            Tenant.id == lease.tenant_id
        ).first()

        if tenant:
            tenant_user = db.query(User).filter(
                User.email == tenant.email
            ).first()

            if tenant_user:
                background_tasks.add_task(
                    notify_rent_due,
                    tenant_user.id,
                    invoice.billing_month,
                    invoice.due_date,
                    invoice.total_amount,
                )

    return invoice


@router.get(
    "/invoices",
    response_model=list[RentInvoiceResponse],
)
def get_rent_invoices_api(
    lease_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_overdue_invoices(db)

    query = db.query(RentInvoice)

    if lease_id is not None:
        query = query.filter(
            RentInvoice.lease_id == lease_id
        )

    if status is not None:
        if status not in INVOICE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid invoice status",
            )

        query = query.filter(
            RentInvoice.status == status
        )

    return query.order_by(
        RentInvoice.id
    ).all()


@router.get(
    "/invoices/{invoice_id}",
    response_model=RentInvoiceResponse,
)
def get_rent_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    update_overdue_invoices(db)

    return get_invoice_or_404(
        db=db,
        invoice_id=invoice_id,
    )


@router.post(
    "/pay/{invoice_id}",
    response_model=PaymentResponse,
)
def pay_rent_invoice(
    invoice_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    update_overdue_invoices(db)

    invoice = get_invoice_or_404(
        db=db,
        invoice_id=invoice_id,
    )

    if payment_data.invoice_id != invoice_id:
        raise HTTPException(
            status_code=400,
            detail="Invoice ID does not match payment request",
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

    existing_payment = db.query(
        Payment
    ).filter(
        Payment.transaction_reference
        == payment_data.transaction_reference
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="Transaction reference already exists",
        )

    successful_payments = db.query(
        Payment
    ).filter(
        Payment.invoice_id == invoice.id,
        Payment.payment_status == "Success",
    ).all()

    total_paid = sum(
        payment.amount
        for payment in successful_payments
    )

    remaining_amount = (
        invoice.total_amount
        - total_paid
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
        invoice_id=invoice_id,
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
                total_paid
                + payment_data.amount
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

    return payment


@router.get(
    "/payments",
    response_model=list[PaymentResponse],
)
def get_rent_payments(
    invoice_id: int | None = None,
    payment_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Payment)

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

    return query.order_by(
        Payment.id
    ).all()