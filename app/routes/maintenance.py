from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.maintenance_request import MaintenanceRequest
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.user import User
from app.schemas.maintenance_request import (
    MaintenanceRequestCreate,
    MaintenanceRequestResponse,
)
from app.services.audit import create_audit_log
from app.services.notifications import notify_maintenance_update
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/maintenance",
    tags=["Maintenance"],
)


MAINTENANCE_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Emergency",
}


MAINTENANCE_STATUSES = {
    "Open",
    "Assigned",
    "In Progress",
    "Resolved",
    "Closed",
}


MAINTENANCE_STAFF_ROLES = {
    "Maintenance Staff",
    "Facility Manager",
}


def get_request_or_404(
    db: Session,
    request_id: int,
):
    maintenance_request = db.query(
        MaintenanceRequest
    ).filter(
        MaintenanceRequest.id == request_id
    ).first()

    if not maintenance_request:
        raise HTTPException(
            status_code=404,
            detail="Maintenance request not found",
        )

    return maintenance_request


def validate_priority(priority: str):
    if priority not in MAINTENANCE_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid maintenance priority",
        )


def validate_status(status: str):
    if status not in MAINTENANCE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid maintenance status",
        )


def validate_staff(
    db: Session,
    staff_id: int,
):
    staff = db.query(User).filter(
        User.id == staff_id
    ).first()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="Maintenance staff not found",
        )

    if not staff.is_active:
        raise HTTPException(
            status_code=400,
            detail="Maintenance staff account is inactive",
        )

    if staff.role not in MAINTENANCE_STAFF_ROLES:
        raise HTTPException(
            status_code=400,
            detail="User is not maintenance staff",
        )

    return staff


@router.post(
    "/requests",
    response_model=MaintenanceRequestResponse,
)
def create_request(
    request_data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    unit = db.query(Unit).filter(
        Unit.id == request_data.unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found",
        )

    if request_data.tenant_id is not None:
        tenant = db.query(Tenant).filter(
            Tenant.id == request_data.tenant_id
        ).first()

        if not tenant:
            raise HTTPException(
                status_code=404,
                detail="Tenant not found",
            )

    validate_priority(
        request_data.priority
    )

    validate_status(
        request_data.status
    )

    if request_data.assigned_staff is not None:
        validate_staff(
            db=db,
            staff_id=request_data.assigned_staff,
        )

    maintenance_request = MaintenanceRequest(
        unit_id=request_data.unit_id,
        tenant_id=request_data.tenant_id,
        category=request_data.category,
        title=request_data.title,
        description=request_data.description,
        priority=request_data.priority,
        assigned_staff=request_data.assigned_staff,
        estimated_cost=request_data.estimated_cost,
        actual_cost=request_data.actual_cost,
        status=request_data.status,
    )

    db.add(maintenance_request)
    db.commit()
    db.refresh(maintenance_request)

    # Audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="MaintenanceRequest",
        entity_id=maintenance_request.id,
        description=(
            f"Created maintenance request "
            f"'{maintenance_request.title}'"
        ),
    )

    return maintenance_request


@router.get(
    "/requests",
    response_model=list[MaintenanceRequestResponse],
)
def get_requests(
    unit_id: int | None = None,
    tenant_id: int | None = None,
    priority: str | None = None,
    status: str | None = None,
    assigned_staff: int | None = None,
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
            "^(id|priority|status|estimated_cost|actual_cost)$"
        ),
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MaintenanceRequest)

    if unit_id is not None:
        query = query.filter(
            MaintenanceRequest.unit_id == unit_id
        )

    if tenant_id is not None:
        query = query.filter(
            MaintenanceRequest.tenant_id == tenant_id
        )

    if priority is not None:
        validate_priority(priority)

        query = query.filter(
            MaintenanceRequest.priority == priority
        )

    if status is not None:
        validate_status(status)

        query = query.filter(
            MaintenanceRequest.status == status
        )

    if assigned_staff is not None:
        query = query.filter(
            MaintenanceRequest.assigned_staff
            == assigned_staff
        )

    sort_column = getattr(
        MaintenanceRequest,
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
    "/requests/{request_id}",
    response_model=MaintenanceRequestResponse,
)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_request_or_404(
        db=db,
        request_id=request_id,
    )


@router.put(
    "/requests/{request_id}/assign",
    response_model=MaintenanceRequestResponse,
)
def assign_request(
    request_id: int,
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
        )
    ),
):
    maintenance_request = get_request_or_404(
        db=db,
        request_id=request_id,
    )

    staff = validate_staff(
        db=db,
        staff_id=staff_id,
    )

    maintenance_request.assigned_staff = staff_id

    if maintenance_request.status == "Open":
        maintenance_request.status = "Assigned"

    db.commit()
    db.refresh(maintenance_request)

    # Audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="ASSIGN",
        entity_type="MaintenanceRequest",
        entity_id=maintenance_request.id,
        description=(
            f"Assigned maintenance request "
            f"'{maintenance_request.title}' "
            f"to staff user {staff.id}"
        ),
    )

    return maintenance_request


@router.put(
    "/requests/{request_id}/status",
    response_model=MaintenanceRequestResponse,
)
def update_status(
    request_id: int,
    status: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
            "Maintenance Staff",
        )
    ),
):
    maintenance_request = get_request_or_404(
        db=db,
        request_id=request_id,
    )

    validate_status(status)

    old_status = maintenance_request.status

    maintenance_request.status = status

    db.commit()
    db.refresh(maintenance_request)

    # Audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE_STATUS",
        entity_type="MaintenanceRequest",
        entity_id=maintenance_request.id,
        description=(
            f"Maintenance request "
            f"'{maintenance_request.title}' "
            f"status changed from "
            f"'{old_status}' to '{status}'"
        ),
    )

    # Notify the tenant after the status change.
    if maintenance_request.tenant_id is not None:
        background_tasks.add_task(
            notify_maintenance_update,
            maintenance_request.tenant_id,
            maintenance_request.id,
            maintenance_request.status,
        )

    return maintenance_request