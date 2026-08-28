from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lease import Lease
from app.models.rent_invoice import RentInvoice
from app.models.user import User
from app.schemas.rent_invoice import (
    RentInvoiceCreate,
    RentInvoiceResponse,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/rent-invoices",
    tags=["Rent Invoices"],
)


INVOICE_STATUSES = {
    "Pending",
    "Paid",
    "Overdue",
    "Cancelled",
}


def calculate_total_amount(
    rent_amount: float,
    late_fee: float,
    discount: float,
) -> float:
    """
    Calculate invoice total.

    Total = Rent + Late Fee - Discount
    """
    return (
        rent_amount
        + late_fee
        - discount
    )


def validate_invoice_data(
    invoice_data: RentInvoiceCreate,
):
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


def get_lease(
    db: Session,
    lease_id: int,
) -> Lease:
    lease = db.query(Lease).filter(
        Lease.id == lease_id
    ).first()

    if not lease:
        raise HTTPException(
            status_code=404,
            detail="Lease not found",
        )

    return lease


def check_duplicate_invoice(
    db: Session,
    lease_id: int,
    billing_month: str,
):
    existing_invoice = db.query(
        RentInvoice
    ).filter(
        RentInvoice.lease_id == lease_id,
        RentInvoice.billing_month == billing_month,
    ).first()

    if existing_invoice:
        raise HTTPException(
            status_code=409,
            detail=(
                "Rent invoice already exists "
                "for this billing month"
            ),
        )


def create_invoice(
    db: Session,
    invoice_data: RentInvoiceCreate,
    user_id: int,
) -> RentInvoice:

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

    # Create audit log after successful invoice creation.
    create_audit_log(
        db=db,
        user_id=user_id,
        action="CREATE",
        entity_type="RentInvoice",
        entity_id=invoice.id,
        description=(
            f"Rent invoice #{invoice.id} created "
            f"for lease #{invoice.lease_id}. "
            f"Billing month: {invoice.billing_month}, "
            f"total amount: {invoice.total_amount:.2f}, "
            f"status: {invoice.status}."
        ),
    )

    return invoice


@router.post(
    "",
    response_model=RentInvoiceResponse,
)
def create_rent_invoice(
    invoice_data: RentInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    # Check that lease exists.
    get_lease(
        db=db,
        lease_id=invoice_data.lease_id,
    )

    # Validate invoice fields.
    validate_invoice_data(
        invoice_data
    )

    # Prevent duplicate invoice.
    check_duplicate_invoice(
        db=db,
        lease_id=invoice_data.lease_id,
        billing_month=invoice_data.billing_month,
    )

    return create_invoice(
        db=db,
        invoice_data=invoice_data,
        user_id=current_user.id,
    )


@router.post(
    "/generate",
    response_model=RentInvoiceResponse,
)
def generate_rent_invoice(
    invoice_data: RentInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    """
    Generate a rent invoice for a lease.

    Required assignment endpoint:

    POST /rent-invoices/generate
    """

    # Check that lease exists.
    lease = get_lease(
        db=db,
        lease_id=invoice_data.lease_id,
    )

    # If rent is not explicitly supplied correctly,
    # use the lease monthly rent.
    if invoice_data.rent_amount <= 0:
        invoice_data.rent_amount = lease.monthly_rent

    # Validate invoice fields after setting rent amount.
    validate_invoice_data(
        invoice_data
    )

    # Prevent duplicate invoice.
    check_duplicate_invoice(
        db=db,
        lease_id=invoice_data.lease_id,
        billing_month=invoice_data.billing_month,
    )

    return create_invoice(
        db=db,
        invoice_data=invoice_data,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[RentInvoiceResponse],
)
def get_rent_invoices(
    lease_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    "/{invoice_id}",
    response_model=RentInvoiceResponse,
)
def get_rent_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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