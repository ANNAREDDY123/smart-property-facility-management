from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.maintenance_request import MaintenanceRequest
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.user import User
from app.schemas.maintenance_request import (
    MaintenanceRequestCreate,
    MaintenanceRequestResponse,
    MaintenanceRequestUpdate,
)
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/maintenance-requests",
    tags=["Maintenance Requests"],
)


MAINTENANCE_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
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


def get_tenant_or_404(
    db: Session,
    tenant_id: int,
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


def get_staff_or_404(
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


@router.post(
    "",
    response_model=MaintenanceRequestResponse,
)
def create_maintenance_request(
    request_data: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_unit_or_404(
        db=db,
        unit_id=request_data.unit_id,
    )

    if request_data.tenant_id is not None:
        get_tenant_or_404(
            db=db,
            tenant_id=request_data.tenant_id,
        )

    validate_priority(
        request_data.priority
    )

    validate_status(
        request_data.status
    )

    if request_data.assigned_staff is not None:
        get_staff_or_404(
            db=db,
            staff_id=request_data.assigned_staff,
        )

    if (
        request_data.priority == "Emergency"
        and request_data.status == "Open"
    ):
        request_status = "Open"
    else:
        request_status = request_data.status

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
        status=request_status,
    )

    db.add(maintenance_request)
    db.commit()
    db.refresh(maintenance_request)

    return maintenance_request


@router.get(
    "",
    response_model=list[MaintenanceRequestResponse],
)
def get_maintenance_requests(
    unit_id: int | None = None,
    tenant_id: int | None = None,
    priority: str | None = None,
    status: str | None = None,
    assigned_staff: int | None = None,
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

    return query.order_by(
        MaintenanceRequest.id
    ).all()


@router.get(
    "/{request_id}",
    response_model=MaintenanceRequestResponse,
)
def get_maintenance_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


@router.put(
    "/{request_id}",
    response_model=MaintenanceRequestResponse,
)
def update_maintenance_request(
    request_id: int,
    request_data: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
        )
    ),
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

    if request_data.priority is not None:
        validate_priority(
            request_data.priority
        )

        maintenance_request.priority = (
            request_data.priority
        )

    if request_data.status is not None:
        validate_status(
            request_data.status
        )

        maintenance_request.status = (
            request_data.status
        )

    if request_data.assigned_staff is not None:
        get_staff_or_404(
            db=db,
            staff_id=request_data.assigned_staff,
        )

        maintenance_request.assigned_staff = (
            request_data.assigned_staff
        )

    if request_data.category is not None:
        maintenance_request.category = (
            request_data.category
        )

    if request_data.title is not None:
        maintenance_request.title = (
            request_data.title
        )

    if request_data.description is not None:
        maintenance_request.description = (
            request_data.description
        )

    if request_data.estimated_cost is not None:
        maintenance_request.estimated_cost = (
            request_data.estimated_cost
        )

    if request_data.actual_cost is not None:
        maintenance_request.actual_cost = (
            request_data.actual_cost
        )

    db.commit()
    db.refresh(maintenance_request)

    return maintenance_request


@router.put(
    "/{request_id}/assign",
    response_model=MaintenanceRequestResponse,
)
def assign_maintenance_request(
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

    get_staff_or_404(
        db=db,
        staff_id=staff_id,
    )

    maintenance_request.assigned_staff = staff_id

    if maintenance_request.status == "Open":
        maintenance_request.status = "Assigned"

    db.commit()
    db.refresh(maintenance_request)

    return maintenance_request


@router.put(
    "/{request_id}/status",
    response_model=MaintenanceRequestResponse,
)
def update_maintenance_status(
    request_id: int,
    status: str,
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

    validate_status(status)

    maintenance_request.status = status

    db.commit()
    db.refresh(maintenance_request)

    return maintenance_request


@router.delete(
    "/{request_id}",
)
def delete_maintenance_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
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

    db.delete(maintenance_request)
    db.commit()

    return {
        "message": "Maintenance request deleted successfully"
    }