from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.maintenance_request import MaintenanceRequest
from app.models.user import User
from app.models.work_order import WorkOrder
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderResponse,
    WorkOrderUpdate,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/work-orders",
    tags=["Work Orders"],
)


WORK_ORDER_PRIORITIES = {
    "Low",
    "Medium",
    "High",
    "Critical",
}


WORK_ORDER_STATUSES = {
    "Pending",
    "Assigned",
    "In Progress",
    "Completed",
    "Cancelled",
}


@router.post(
    "",
    response_model=WorkOrderResponse,
)
def create_work_order(
    work_order_data: WorkOrderCreate,
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
        MaintenanceRequest.id
        == work_order_data.maintenance_request_id
    ).first()

    if not maintenance_request:
        raise HTTPException(
            status_code=404,
            detail="Maintenance request not found",
        )

    if work_order_data.assigned_to is not None:
        assigned_user = db.query(User).filter(
            User.id == work_order_data.assigned_to
        ).first()

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found",
            )

    if work_order_data.priority not in WORK_ORDER_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail="Invalid work order priority",
        )

    if work_order_data.status not in WORK_ORDER_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid work order status",
        )

    work_order = WorkOrder(
        maintenance_request_id=(
            work_order_data.maintenance_request_id
        ),
        assigned_to=work_order_data.assigned_to,
        title=work_order_data.title,
        description=work_order_data.description,
        priority=work_order_data.priority,
        status=work_order_data.status,
        scheduled_date=work_order_data.scheduled_date,
    )

    db.add(work_order)
    db.commit()
    db.refresh(work_order)

    # Create audit log after successful work order creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="WorkOrder",
        entity_id=work_order.id,
        description=(
            f"Work order #{work_order.id} created. "
            f"Title: {work_order.title}, "
            f"maintenance request "
            f"#{work_order.maintenance_request_id}, "
            f"status: {work_order.status}, "
            f"priority: {work_order.priority}."
        ),
    )

    return work_order


@router.get(
    "",
    response_model=list[WorkOrderResponse],
)
def get_work_orders(
    maintenance_request_id: int | None = None,
    assigned_to: int | None = None,
    priority: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WorkOrder)

    if maintenance_request_id is not None:
        query = query.filter(
            WorkOrder.maintenance_request_id
            == maintenance_request_id
        )

    if assigned_to is not None:
        query = query.filter(
            WorkOrder.assigned_to == assigned_to
        )

    if priority is not None:
        if priority not in WORK_ORDER_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail="Invalid work order priority",
            )

        query = query.filter(
            WorkOrder.priority == priority
        )

    if status is not None:
        if status not in WORK_ORDER_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid work order status",
            )

        query = query.filter(
            WorkOrder.status == status
        )

    return query.order_by(
        WorkOrder.id
    ).all()


@router.get(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    work_order = db.query(WorkOrder).filter(
        WorkOrder.id == work_order_id
    ).first()

    if not work_order:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    return work_order


@router.put(
    "/{work_order_id}",
    response_model=WorkOrderResponse,
)
def update_work_order(
    work_order_id: int,
    work_order_data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    work_order = db.query(WorkOrder).filter(
        WorkOrder.id == work_order_id
    ).first()

    if not work_order:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    changed_fields = []

    if work_order_data.assigned_to is not None:
        assigned_user = db.query(User).filter(
            User.id == work_order_data.assigned_to
        ).first()

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found",
            )

        if work_order.assigned_to != work_order_data.assigned_to:
            changed_fields.append("assigned_to")

        work_order.assigned_to = (
            work_order_data.assigned_to
        )

    if work_order_data.title is not None:
        if work_order.title != work_order_data.title:
            changed_fields.append("title")

        work_order.title = work_order_data.title

    if work_order_data.description is not None:
        if work_order.description != work_order_data.description:
            changed_fields.append("description")

        work_order.description = (
            work_order_data.description
        )

    if work_order_data.priority is not None:
        if work_order_data.priority not in WORK_ORDER_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail="Invalid work order priority",
            )

        if work_order.priority != work_order_data.priority:
            changed_fields.append("priority")

        work_order.priority = work_order_data.priority

    if work_order_data.status is not None:
        if work_order_data.status not in WORK_ORDER_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid work order status",
            )

        if work_order.status != work_order_data.status:
            changed_fields.append("status")

        work_order.status = work_order_data.status

        if work_order_data.status == "Completed":
            work_order.completed_at = datetime.now()

    if work_order_data.scheduled_date is not None:
        if work_order.scheduled_date != work_order_data.scheduled_date:
            changed_fields.append("scheduled_date")

        work_order.scheduled_date = (
            work_order_data.scheduled_date
        )

    if work_order_data.completed_at is not None:
        if work_order.completed_at != work_order_data.completed_at:
            changed_fields.append("completed_at")

        work_order.completed_at = (
            work_order_data.completed_at
        )

    db.commit()
    db.refresh(work_order)

    # Create audit log after successful work order update.
    if changed_fields:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            entity_type="WorkOrder",
            entity_id=work_order.id,
            description=(
                f"Work order #{work_order.id} "
                f"was updated. "
                f"Changed fields: "
                f"{', '.join(changed_fields)}."
            ),
        )

    return work_order


@router.delete(
    "/{work_order_id}",
)
def delete_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    work_order = db.query(WorkOrder).filter(
        WorkOrder.id == work_order_id
    ).first()

    if not work_order:
        raise HTTPException(
            status_code=404,
            detail="Work order not found",
        )

    work_order_title = work_order.title
    work_order_id_value = work_order.id

    db.delete(work_order)
    db.commit()

    # Create audit log after successful work order deletion.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="WorkOrder",
        entity_id=work_order_id_value,
        description=(
            f"Work order #{work_order_id_value} "
            f"'{work_order_title}' was deleted."
        ),
    )

    return {
        "message": "Work order deleted successfully"
    }