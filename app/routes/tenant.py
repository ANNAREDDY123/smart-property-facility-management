from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lease import Lease
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import (
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from app.schemas.lease import LeaseResponse
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
)


@router.post(
    "",
    response_model=TenantResponse,
)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    existing_email = db.query(Tenant).filter(
        Tenant.email == tenant_data.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Tenant email already exists",
        )

    existing_id = db.query(Tenant).filter(
        Tenant.identification_number
        == tenant_data.identification_number
    ).first()

    if existing_id:
        raise HTTPException(
            status_code=409,
            detail="Identification number already exists",
        )

    tenant = Tenant(
        full_name=tenant_data.full_name,
        email=tenant_data.email,
        phone=tenant_data.phone,
        identification_number=(
            tenant_data.identification_number
        ),
        emergency_contact=tenant_data.emergency_contact,
        address=tenant_data.address,
    )

    db.add(tenant)

    try:
        db.commit()
        db.refresh(tenant)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Tenant email or identification number "
                "already exists"
            ),
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Tenant",
        entity_id=tenant.id,
        description=(
            f"Tenant '{tenant.full_name}' "
            f"was created."
        ),
    )

    return tenant


@router.get(
    "",
    response_model=list[TenantResponse],
)
def get_tenants(
    name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    unit_id: int | None = Query(default=None, gt=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(
        default="id",
        pattern="^(id|full_name|email)$",
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Tenant)

    if name:
        query = query.filter(
            Tenant.full_name.ilike(f"%{name}%")
        )

    if email:
        query = query.filter(
            Tenant.email.ilike(f"%{email}%")
        )

    if unit_id is not None:
        query = (
            query
            .join(
                Lease,
                Lease.tenant_id == Tenant.id,
            )
            .filter(
                Lease.unit_id == unit_id
            )
        )

    sort_column = getattr(Tenant, sort_by)

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
    "/{tenant_id}/rental-history",
    response_model=list[LeaseResponse],
)
def get_tenant_rental_history(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return (
        db.query(Lease)
        .filter(Lease.tenant_id == tenant_id)
        .order_by(Lease.start_date.desc())
        .all()
    )


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
)
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return tenant


@router.put(
    "/{tenant_id}",
    response_model=TenantResponse,
)
def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    update_data = tenant_data.model_dump(
        exclude_unset=True
    )

    if "email" in update_data:
        existing_email = db.query(Tenant).filter(
            Tenant.email == update_data["email"],
            Tenant.id != tenant_id,
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="Tenant email already exists",
            )

    if "identification_number" in update_data:
        existing_id = db.query(Tenant).filter(
            Tenant.identification_number
            == update_data["identification_number"],
            Tenant.id != tenant_id,
        ).first()

        if existing_id:
            raise HTTPException(
                status_code=409,
                detail="Identification number already exists",
            )

    changed_fields = []

    for field, value in update_data.items():
        old_value = getattr(tenant, field)

        if old_value != value:
            changed_fields.append(field)
            setattr(tenant, field, value)

    try:
        db.commit()
        db.refresh(tenant)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Tenant email or identification number "
                "already exists"
            ),
        )

    if changed_fields:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Tenant",
            entity_id=tenant.id,
            description=(
                f"Tenant '{tenant.full_name}' "
                f"was updated. Fields changed: "
                f"{', '.join(changed_fields)}."
            ),
        )

    return tenant