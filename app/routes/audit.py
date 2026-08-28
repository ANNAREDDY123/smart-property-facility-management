from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.dependencies import get_current_user


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
)
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(
        AuditLog
    ).order_by(
        AuditLog.id.desc()
    ).all()