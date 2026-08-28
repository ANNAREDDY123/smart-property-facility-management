from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.utils.dependencies import require_roles


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


AUDIT_LOG_ROLES = {
    "Super Admin",
    "Property Manager",
}


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    query = db.query(AuditLog)

    if action is not None:
        query = query.filter(
            AuditLog.action == action
        )

    if entity_type is not None:
        query = query.filter(
            AuditLog.entity_type == entity_type
        )

    if entity_id is not None:
        query = query.filter(
            AuditLog.entity_id == entity_id
        )

    if user_id is not None:
        query = query.filter(
            AuditLog.user_id == user_id
        )

    if start_date is not None:
        query = query.filter(
            AuditLog.created_at >= start_date
        )

    if end_date is not None:
        if (
            start_date is not None
            and end_date < start_date
        ):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=400,
                detail=(
                    "end_date cannot be before "
                    "start_date"
                ),
            )

        query = query.filter(
            AuditLog.created_at <= end_date
        )

    if sort_order == "desc":
        query = query.order_by(
            AuditLog.created_at.desc()
        )
    else:
        query = query.order_by(
            AuditLog.created_at.asc()
        )

    offset = (page - 1) * limit

    return (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get(
    "/{audit_log_id}",
    response_model=AuditLogResponse,
)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    from fastapi import HTTPException

    audit_log = db.query(AuditLog).filter(
        AuditLog.id == audit_log_id
    ).first()

    if not audit_log:
        raise HTTPException(
            status_code=404,
            detail="Audit log not found",
        )

    return audit_log