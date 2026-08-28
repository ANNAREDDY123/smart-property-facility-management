from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lease import Lease
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.user import User
from app.schemas.lease import (
    LeaseCreate,
    LeaseResponse,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/leases",
    tags=["Leases"],
)


LEASE_STATUSES = {
    "Draft",
    "Active",
    "Expired",
    "Terminated",
}


@router.post(
    "",
    response_model=LeaseResponse,
)
def create_lease(
    lease_data: LeaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    tenant = db.query(Tenant).filter(
        Tenant.id == lease_data.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    unit = db.query(Unit).filter(
        Unit.id == lease_data.unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found",
        )

    if lease_data.lease_status not in LEASE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid lease status",
        )

    if unit.status == "Maintenance":
        raise HTTPException(
            status_code=400,
            detail="Maintenance units cannot be leased",
        )

    # Check for overlapping active leases.
    overlapping_lease = db.query(Lease).filter(
        Lease.unit_id == lease_data.unit_id,
        Lease.lease_status == "Active",
        Lease.start_date <= lease_data.end_date,
        Lease.end_date >= lease_data.start_date,
    ).first()

    if overlapping_lease:
        raise HTTPException(
            status_code=409,
            detail="Unit already has an overlapping active lease",
        )

    # An occupied unit cannot receive another active lease.
    if (
        unit.status == "Occupied"
        and lease_data.lease_status == "Active"
    ):
        raise HTTPException(
            status_code=409,
            detail="Occupied unit cannot have another active lease",
        )

    lease = Lease(
        tenant_id=lease_data.tenant_id,
        unit_id=lease_data.unit_id,
        start_date=lease_data.start_date,
        end_date=lease_data.end_date,
        monthly_rent=lease_data.monthly_rent,
        security_deposit=lease_data.security_deposit,
        lease_status=lease_data.lease_status,
    )

    db.add(lease)

    # Active lease → Occupied unit
    if lease.lease_status == "Active":
        unit.status = "Occupied"

    db.commit()
    db.refresh(lease)

    # Create audit log after lease is successfully created.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Lease",
        entity_id=lease.id,
        description=(
            f"Lease #{lease.id} created for "
            f"tenant #{lease.tenant_id} and "
            f"unit #{lease.unit_id}."
        ),
    )

    return lease


@router.get(
    "",
    response_model=list[LeaseResponse],
)
def get_leases(
    tenant_id: int | None = None,
    unit_id: int | None = None,
    lease_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Lease)

    if tenant_id is not None:
        query = query.filter(
            Lease.tenant_id == tenant_id
        )

    if unit_id is not None:
        query = query.filter(
            Lease.unit_id == unit_id
        )

    if lease_status is not None:
        if lease_status not in LEASE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid lease status",
            )

        query = query.filter(
            Lease.lease_status == lease_status
        )

    return query.order_by(Lease.id).all()


@router.get(
    "/{lease_id}",
    response_model=LeaseResponse,
)
def get_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id
    ).first()

    if not lease:
        raise HTTPException(
            status_code=404,
            detail="Lease not found",
        )

    return lease


@router.put(
    "/{lease_id}/terminate",
    response_model=LeaseResponse,
)
def terminate_lease(
    lease_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    lease = db.query(Lease).filter(
        Lease.id == lease_id
    ).first()

    if not lease:
        raise HTTPException(
            status_code=404,
            detail="Lease not found",
        )

    if lease.lease_status == "Terminated":
        raise HTTPException(
            status_code=400,
            detail="Lease is already terminated",
        )

    lease.lease_status = "Terminated"

    unit = db.query(Unit).filter(
        Unit.id == lease.unit_id
    ).first()

    if unit and unit.status == "Occupied":
        unit.status = "Available"

    db.commit()
    db.refresh(lease)

    # Create audit log after successful termination.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="TERMINATE",
        entity_type="Lease",
        entity_id=lease.id,
        description=(
            f"Lease #{lease.id} terminated. "
            f"Tenant #{lease.tenant_id}, "
            f"unit #{lease.unit_id}."
        ),
    )

    return lease