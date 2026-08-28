from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.parking import Parking
from app.models.property import Property
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.parking import (
    PARKING_STATUSES,
    ParkingAssign,
    ParkingCreate,
    ParkingResponse,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/parking",
    tags=["Parking"],
)


@router.post(
    "",
    response_model=ParkingResponse,
)
def create_parking(
    parking_data: ParkingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    property_obj = db.query(Property).filter(
        Property.id == parking_data.property_id
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    existing = db.query(Parking).filter(
        Parking.property_id == parking_data.property_id,
        Parking.parking_number == parking_data.parking_number,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Parking number already exists in this property",
        )

    parking = Parking(
        property_id=parking_data.property_id,
        parking_number=parking_data.parking_number,
        status=parking_data.status,
    )

    db.add(parking)

    try:
        db.commit()
        db.refresh(parking)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Parking number already exists in this property",
        )

    # Create audit log after successful parking creation.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Parking",
        entity_id=parking.id,
        description=(
            f"Parking slot #{parking.id} created. "
            f"Property #{parking.property_id}, "
            f"parking number: {parking.parking_number}."
        ),
    )

    return parking


@router.get(
    "",
    response_model=list[ParkingResponse],
)
def get_parking(
    property_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Parking)

    if property_id is not None:
        query = query.filter(
            Parking.property_id == property_id
        )

    if status is not None:
        if status not in PARKING_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid parking status",
            )

        query = query.filter(
            Parking.status == status
        )

    return query.order_by(
        Parking.id
    ).all()


@router.post(
    "/{parking_id}/assign",
    response_model=ParkingResponse,
)
def assign_parking(
    parking_id: int,
    assignment_data: ParkingAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    parking = db.query(Parking).filter(
        Parking.id == parking_id
    ).first()

    if not parking:
        raise HTTPException(
            status_code=404,
            detail="Parking slot not found",
        )

    if parking.status == "Blocked":
        raise HTTPException(
            status_code=400,
            detail="Blocked parking slot cannot be assigned",
        )

    if parking.status == "Assigned":
        raise HTTPException(
            status_code=400,
            detail="Parking slot is already assigned",
        )

    tenant = db.query(Tenant).filter(
        Tenant.id == assignment_data.tenant_id
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    existing_vehicle = db.query(Parking).filter(
        Parking.vehicle_number == assignment_data.vehicle_number,
        Parking.status == "Assigned",
        Parking.id != parking_id,
    ).first()

    if existing_vehicle:
        raise HTTPException(
            status_code=409,
            detail="Vehicle is already assigned to another parking slot",
        )

    parking.vehicle_number = assignment_data.vehicle_number
    parking.vehicle_type = assignment_data.vehicle_type
    parking.tenant_id = assignment_data.tenant_id
    parking.status = "Assigned"

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Vehicle number already exists",
        )

    db.refresh(parking)

    # Create audit log after successful parking assignment.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="ASSIGN",
        entity_type="Parking",
        entity_id=parking.id,
        description=(
            f"Parking slot #{parking.id} assigned to "
            f"tenant #{parking.tenant_id}. "
            f"Vehicle: {parking.vehicle_number}."
        ),
    )

    return parking


@router.put(
    "/{parking_id}/release",
    response_model=ParkingResponse,
)
def release_parking(
    parking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    parking = db.query(Parking).filter(
        Parking.id == parking_id
    ).first()

    if not parking:
        raise HTTPException(
            status_code=404,
            detail="Parking slot not found",
        )

    if parking.status != "Assigned":
        raise HTTPException(
            status_code=400,
            detail="Parking slot is not assigned",
        )

    parking.vehicle_number = None
    parking.vehicle_type = None
    parking.tenant_id = None
    parking.status = "Available"

    db.commit()
    db.refresh(parking)

    # Create audit log after successful parking release.
    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="RELEASE",
        entity_type="Parking",
        entity_id=parking.id,
        description=(
            f"Parking slot #{parking.id} released "
            f"and returned to Available status."
        ),
    )

    return parking