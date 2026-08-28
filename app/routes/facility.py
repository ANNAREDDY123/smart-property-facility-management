from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.facility import Facility
from app.models.facility_booking import FacilityBooking
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.facility import (
    BOOKING_STATUSES,
    FACILITY_STATUSES,
    FACILITY_TYPES,
    FacilityBookingCreate,
    FacilityBookingResponse,
    FacilityCreate,
    FacilityResponse,
)
from app.services.audit import create_audit_log
from app.services.notifications import notify_facility_booking
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/facilities",
    tags=["Facilities"],
)


@router.post(
    "",
    response_model=FacilityResponse,
)
def create_facility(
    facility_data: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
            "Facility Manager",
        )
    ),
):
    existing = db.query(Facility).filter(
        Facility.name == facility_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Facility already exists",
        )

    facility = Facility(
        name=facility_data.name,
        capacity=facility_data.capacity,
        status=facility_data.status,
    )

    db.add(facility)
    db.commit()
    db.refresh(facility)

    # Create audit log after successful facility creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Facility",
        entity_id=facility.id,
        description=(
            f"Facility #{facility.id} created. "
            f"Name: {facility.name}, "
            f"capacity: {facility.capacity}, "
            f"status: {facility.status}."
        ),
    )

    return facility


@router.get(
    "",
    response_model=list[FacilityResponse],
)
def get_facilities(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Facility)

    if status is not None:
        if status not in FACILITY_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid facility status",
            )

        query = query.filter(
            Facility.status == status
        )

    return query.order_by(Facility.id).all()


@router.post(
    "/{facility_id}/book",
    response_model=FacilityBookingResponse,
)
def book_facility(
    facility_id: int,
    booking_data: FacilityBookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    facility = db.query(Facility).filter(
        Facility.id == facility_id
    ).first()

    if not facility:
        raise HTTPException(
            status_code=404,
            detail="Facility not found",
        )

    if facility.status != "Active":
        raise HTTPException(
            status_code=400,
            detail="Facility is not active",
        )

    tenant = db.query(Tenant).filter(
        Tenant.id == booking_data.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    if booking_data.end_time <= booking_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time",
        )

    overlapping_bookings = db.query(
        FacilityBooking
    ).filter(
        FacilityBooking.facility_id == facility_id,
        FacilityBooking.booking_date
        == booking_data.booking_date,
        FacilityBooking.status != "Cancelled",
        FacilityBooking.start_time
        < booking_data.end_time,
        FacilityBooking.end_time
        > booking_data.start_time,
    ).all()

    if len(overlapping_bookings) >= facility.capacity:
        raise HTTPException(
            status_code=409,
            detail="Facility capacity exceeded for this time slot",
        )

    booking = FacilityBooking(
        facility_id=facility_id,
        tenant_id=booking_data.tenant_id,
        booking_date=booking_data.booking_date,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        status=booking_data.status,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Create audit log after successful facility booking.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="BOOK",
        entity_type="FacilityBooking",
        entity_id=booking.id,
        description=(
            f"Facility booking #{booking.id} created "
            f"for facility #{booking.facility_id}. "
            f"Tenant #{booking.tenant_id}, "
            f"date: {booking.booking_date}, "
            f"time: {booking.start_time} - "
            f"{booking.end_time}, "
            f"status: {booking.status}."
        ),
    )

    # Send facility booking confirmation in the background.
    if booking.status == "Confirmed":
        background_tasks.add_task(
            notify_facility_booking,
            tenant.id,
            facility.name,
            booking.booking_date,
        )

    return booking


@router.get(
    "/bookings",
    response_model=list[FacilityBookingResponse],
)
def get_facility_bookings(
    facility_id: int | None = None,
    tenant_id: int | None = None,
    booking_date: date | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(FacilityBooking)

    if facility_id is not None:
        query = query.filter(
            FacilityBooking.facility_id == facility_id
        )

    if tenant_id is not None:
        query = query.filter(
            FacilityBooking.tenant_id == tenant_id
        )

    if booking_date is not None:
        query = query.filter(
            FacilityBooking.booking_date == booking_date
        )

    if status is not None:
        if status not in BOOKING_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid booking status",
            )

        query = query.filter(
            FacilityBooking.status == status
        )

    return query.order_by(
        FacilityBooking.id
    ).all()