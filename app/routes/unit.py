from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.building import Building
from app.models.unit import Unit
from app.models.user import User
from app.schemas.unit import (
    UNIT_STATUSES,
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/units",
    tags=["Units"],
)


@router.post(
    "",
    response_model=UnitResponse,
)
def create_unit(
    unit_data: UnitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    building = db.query(Building).filter(
        Building.id == unit_data.building_id
    ).first()

    if not building:
        raise HTTPException(
            status_code=404,
            detail="Building not found",
        )

    if unit_data.status not in UNIT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid unit status. Allowed values: "
                "Available, Occupied, Reserved, Maintenance"
            ),
        )

    existing_unit = db.query(Unit).filter(
        Unit.building_id == unit_data.building_id,
        Unit.unit_number == unit_data.unit_number,
    ).first()

    if existing_unit:
        raise HTTPException(
            status_code=409,
            detail="Unit number already exists in this building",
        )

    unit = Unit(
        building_id=unit_data.building_id,
        unit_number=unit_data.unit_number,
        floor_number=unit_data.floor_number,
        unit_type=unit_data.unit_type,
        area=unit_data.area,
        monthly_rent=unit_data.monthly_rent,
        status=unit_data.status,
    )

    db.add(unit)

    try:
        db.commit()
        db.refresh(unit)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unit number already exists in this building",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Unit",
        entity_id=unit.id,
        description=(
            f"Unit '{unit.unit_number}' "
            f"was created."
        ),
    )

    return unit


@router.get(
    "",
    response_model=list[UnitResponse],
)
def get_units(
    building_id: int | None = None,
    unit_type: str | None = None,
    status: str | None = None,
    min_rent: float | None = None,
    max_rent: float | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(
        default="id",
        pattern="^(id|unit_number|floor_number|area|monthly_rent)$",
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Unit)

    if building_id is not None:
        query = query.filter(
            Unit.building_id == building_id
        )

    if unit_type:
        query = query.filter(
            Unit.unit_type.ilike(f"%{unit_type}%")
        )

    if status is not None:
        if status not in UNIT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid unit status",
            )

        query = query.filter(
            Unit.status == status
        )

    if min_rent is not None:
        if min_rent < 0:
            raise HTTPException(
                status_code=400,
                detail="min_rent cannot be negative",
            )

        query = query.filter(
            Unit.monthly_rent >= min_rent
        )

    if max_rent is not None:
        if max_rent < 0:
            raise HTTPException(
                status_code=400,
                detail="max_rent cannot be negative",
            )

        query = query.filter(
            Unit.monthly_rent <= max_rent
        )

    if (
        min_rent is not None
        and max_rent is not None
        and min_rent > max_rent
    ):
        raise HTTPException(
            status_code=400,
            detail="min_rent cannot be greater than max_rent",
        )

    sort_column = getattr(Unit, sort_by)

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
    "/{unit_id}",
    response_model=UnitResponse,
)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


@router.put(
    "/{unit_id}",
    response_model=UnitResponse,
)
def update_unit(
    unit_id: int,
    unit_data: UnitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    unit = db.query(Unit).filter(
        Unit.id == unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found",
        )

    update_data = unit_data.model_dump(
        exclude_unset=True
    )

    if "status" in update_data:
        if update_data["status"] not in UNIT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid unit status",
            )

    if "unit_number" in update_data:
        existing_unit = db.query(Unit).filter(
            Unit.building_id == unit.building_id,
            Unit.unit_number == update_data["unit_number"],
            Unit.id != unit.id,
        ).first()

        if existing_unit:
            raise HTTPException(
                status_code=409,
                detail="Unit number already exists in this building",
            )

    changed_fields = []

    for field, value in update_data.items():
        old_value = getattr(unit, field)

        if old_value != value:
            changed_fields.append(field)
            setattr(unit, field, value)

    try:
        db.commit()
        db.refresh(unit)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unit number already exists in this building",
        )

    if changed_fields:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="UPDATE",
            entity_type="Unit",
            entity_id=unit.id,
            description=(
                f"Unit '{unit.unit_number}' "
                f"was updated. Fields changed: "
                f"{', '.join(changed_fields)}."
            ),
        )

    return unit