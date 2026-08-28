from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int | None,
    description: str,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log