from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def _run_notification(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
):
    """
    Background task entry point.

    Creates its own database session so it does not use
    the request-scoped SQLAlchemy session.
    """
    db = SessionLocal()

    try:
        create_notification(
            db=db,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )
    finally:
        db.close()


def notify_rent_due(
    user_id: int,
    billing_month: str,
    due_date,
    amount: float,
):
    _run_notification(
        user_id=user_id,
        notification_type="Rent Due",
        title="Rent Payment Due",
        message=(
            f"Rent for {billing_month} is due on "
            f"{due_date}. Amount due: {amount:.2f}."
        ),
    )


def notify_rent_overdue(
    user_id: int,
    billing_month: str,
    amount: float,
):
    _run_notification(
        user_id=user_id,
        notification_type="Rent Overdue",
        title="Rent Payment Overdue",
        message=(
            f"Rent for {billing_month} is overdue. "
            f"Outstanding amount: {amount:.2f}."
        ),
    )


def notify_maintenance_update(
    user_id: int,
    request_id: int,
    status: str,
):
    _run_notification(
        user_id=user_id,
        notification_type="Maintenance Update",
        title="Maintenance Request Updated",
        message=(
            f"Maintenance request #{request_id} "
            f"has been updated to {status}."
        ),
    )


def notify_visitor_approval(
    user_id: int,
    visitor_name: str,
):
    _run_notification(
        user_id=user_id,
        notification_type="Visitor Approval",
        title="Visitor Update",
        message=(
            f"Visitor {visitor_name} has been approved."
        ),
    )


def notify_facility_booking(
    user_id: int,
    facility_name: str,
    booking_date,
):
    _run_notification(
        user_id=user_id,
        notification_type="Facility Booking",
        title="Facility Booking Confirmed",
        message=(
            f"Your booking for {facility_name} "
            f"on {booking_date} has been confirmed."
        ),
    )


def notify_lease_expiry(
    user_id: int,
    lease_id: int,
    end_date,
):
    _run_notification(
        user_id=user_id,
        notification_type="Lease Expiry",
        title="Lease Expiry Reminder",
        message=(
            f"Lease #{lease_id} is scheduled to expire "
            f"on {end_date}."
        ),
    )

def check_lease_expiry_notifications():
    from datetime import date, timedelta

    from app.models.lease import Lease
    from app.models.tenant import Tenant
    from app.models.user import User

    db = SessionLocal()

    try:
        today = date.today()
        expiry_limit = today + timedelta(days=30)

        leases = (
            db.query(Lease)
            .filter(
                Lease.lease_status == "Active",
                Lease.end_date >= today,
                Lease.end_date <= expiry_limit,
            )
            .all()
        )

        for lease in leases:
            tenant = db.query(Tenant).filter(
                Tenant.id == lease.tenant_id
            ).first()

            if not tenant:
                continue

            tenant_user = db.query(User).filter(
                User.email == tenant.email
            ).first()

            if not tenant_user:
                continue

            create_notification(
                db=db,
                user_id=tenant_user.id,
                notification_type="Lease Expiry",
                title="Lease Expiry Reminder",
                message=(
                    f"Lease #{lease.id} is scheduled to expire "
                    f"on {lease.end_date}."
                ),
            )

    finally:
        db.close()