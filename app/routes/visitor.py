from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.user import User
from app.models.visitor import Visitor
from app.schemas.visitor import (
    VisitorCreate,
    VisitorResponse,
    VISITOR_STATUSES,
)
from app.services.audit import create_audit_log
from app.services.notifications import notify_visitor_approval
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/visitors",
    tags=["Visitors"],
)


@router.post(
    "",
    response_model=VisitorResponse,
)
def create_visitor(
    visitor_data: VisitorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Security Staff",
            "Tenant",
        )
    ),
):
    tenant = db.query(Tenant).filter(
        Tenant.id == visitor_data.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    unit = db.query(Unit).filter(
        Unit.id == visitor_data.unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found",
        )

    if visitor_data.visitor_status not in VISITOR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid visitor status",
        )

    entry_time = visitor_data.entry_time

    if visitor_data.visitor_status == "Checked In":
        if entry_time is None:
            entry_time = datetime.now(timezone.utc)

    visitor = Visitor(
        visitor_name=visitor_data.visitor_name,
        phone=visitor_data.phone,
        tenant_id=visitor_data.tenant_id,
        unit_id=visitor_data.unit_id,
        purpose=visitor_data.purpose,
        entry_time=entry_time,
        visitor_status=visitor_data.visitor_status,
    )

    db.add(visitor)
    db.commit()
    db.refresh(visitor)

    # Create audit log after successful visitor creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Visitor",
        entity_id=visitor.id,
        description=(
            f"Visitor #{visitor.id} created. "
            f"Visitor name: {visitor.visitor_name}, "
            f"tenant #{visitor.tenant_id}, "
            f"unit #{visitor.unit_id}, "
            f"status: {visitor.visitor_status}."
        ),
    )

    # Notify the tenant when a visitor is approved/confirmed.
    if visitor.visitor_status in {
        "Expected",
        "Checked In",
    }:
        tenant_user = db.query(User).filter(
            User.email == tenant.email
        ).first()

        if tenant_user:
            background_tasks.add_task(
                notify_visitor_approval,
                tenant_user.id,
                visitor.visitor_name,
            )

    return visitor


@router.get(
    "",
    response_model=list[VisitorResponse],
)
def get_visitors(
    tenant_id: int | None = None,
    unit_id: int | None = None,
    visitor_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Visitor)

    if tenant_id is not None:
        query = query.filter(
            Visitor.tenant_id == tenant_id
        )

    if unit_id is not None:
        query = query.filter(
            Visitor.unit_id == unit_id
        )

    if visitor_status is not None:
        if visitor_status not in VISITOR_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid visitor status",
            )

        query = query.filter(
            Visitor.visitor_status == visitor_status
        )

    return query.order_by(
        Visitor.id
    ).all()


@router.put(
    "/{visitor_id}/checkout",
    response_model=VisitorResponse,
)
def checkout_visitor(
    visitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Security Staff",
        )
    ),
):
    visitor = db.query(Visitor).filter(
        Visitor.id == visitor_id
    ).first()

    if not visitor:
        raise HTTPException(
            status_code=404,
            detail="Visitor not found",
        )

    if visitor.visitor_status == "Checked Out":
        raise HTTPException(
            status_code=400,
            detail="Visitor is already checked out",
        )

    if visitor.visitor_status == "Cancelled":
        raise HTTPException(
            status_code=400,
            detail="Cancelled visitor cannot be checked out",
        )

    visitor.exit_time = datetime.now(timezone.utc)
    visitor.visitor_status = "Checked Out"

    db.commit()
    db.refresh(visitor)

    # Create audit log after successful visitor checkout.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CHECKOUT",
        entity_type="Visitor",
        entity_id=visitor.id,
        description=(
            f"Visitor #{visitor.id} checked out. "
            f"Visitor name: {visitor.visitor_name}, "
            f"tenant #{visitor.tenant_id}, "
            f"unit #{visitor.unit_id}."
        ),
    )

    return visitor