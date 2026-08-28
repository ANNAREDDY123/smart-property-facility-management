from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyResponse,
    PropertyUpdate,
)
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/properties",
    tags=["Properties"],
)


ALLOWED_PROPERTY_TYPES = {
    "Apartment",
    "Villa",
    "Commercial",
    "Office",
    "Warehouse",
}


ALLOWED_STATUSES = {
    "Active",
    "Inactive",
    "Under Maintenance",
}


@router.post(
    "",
    response_model=PropertyResponse,
)
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    if property_data.property_type not in ALLOWED_PROPERTY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid property type. Allowed values: "
                "Apartment, Villa, Commercial, Office, Warehouse"
            ),
        )

    if property_data.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid property status. Allowed values: "
                "Active, Inactive, Under Maintenance"
            ),
        )

    property_obj = Property(
        property_name=property_data.property_name,
        property_type=property_data.property_type,
        address=property_data.address,
        city=property_data.city,
        state=property_data.state,
        total_area=property_data.total_area,
        total_units=property_data.total_units,
        status=property_data.status,
        is_deleted=False,
    )

    db.add(property_obj)

    try:
        db.commit()
        db.refresh(property_obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Unable to create property",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Property",
        entity_id=property_obj.id,
        description=(
            f"Property '{property_obj.property_name}' "
            f"was created"
        ),
    )

    return property_obj


@router.get(
    "",
    response_model=list[PropertyResponse],
)
def get_properties(
    search: Optional[str] = Query(
        default=None,
        description="Search by property name",
    ),
    property_type: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(
        default="id",
        pattern=(
            "^(id|property_name|city|total_area|total_units)$"
        ),
    ),
    sort_order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Property).filter(
        Property.is_deleted.is_(False)
    )

    if search:
        query = query.filter(
            Property.property_name.ilike(
                f"%{search}%"
            )
        )

    if property_type:
        query = query.filter(
            Property.property_type == property_type
        )

    if city:
        query = query.filter(
            Property.city.ilike(f"%{city}%")
        )

    if status:
        query = query.filter(
            Property.status == status
        )

    sort_column = getattr(
        Property,
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
    "/{property_id}",
    response_model=PropertyResponse,
)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted.is_(False),
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    return property_obj


@router.put(
    "/{property_id}",
    response_model=PropertyResponse,
)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted.is_(False),
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    update_data = property_data.model_dump(
        exclude_unset=True
    )

    if "property_type" in update_data:
        if (
            update_data["property_type"]
            not in ALLOWED_PROPERTY_TYPES
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid property type",
            )

    if "status" in update_data:
        if update_data["status"] not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Invalid property status",
            )

    old_values = {}

    for field in update_data:
        old_values[field] = getattr(
            property_obj,
            field,
        )

    for field, value in update_data.items():
        setattr(
            property_obj,
            field,
            value,
        )

    try:
        db.commit()
        db.refresh(property_obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Unable to update property",
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="Property",
        entity_id=property_obj.id,
        description=(
            f"Property '{property_obj.property_name}' "
            f"was updated. "
            f"Changed fields: "
            f"{', '.join(update_data.keys())}"
        ),
    )

    return property_obj


@router.delete(
    "/{property_id}",
)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("Super Admin")
    ),
):
    property_obj = db.query(Property).filter(
        Property.id == property_id,
        Property.is_deleted.is_(False),
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    property_name = property_obj.property_name

    property_obj.is_deleted = True

    db.commit()
    db.refresh(property_obj)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="DELETE",
        entity_type="Property",
        entity_id=property_obj.id,
        description=(
            f"Property '{property_name}' "
            f"was soft deleted"
        ),
    )

    return {
        "message": "Property deleted successfully"
    }