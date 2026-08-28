from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.building import Building
from app.models.property import Property
from app.models.user import User
from app.schemas.building import BuildingCreate, BuildingResponse
from app.services.audit import create_audit_log
from app.utils.dependencies import get_current_user, require_roles


router = APIRouter(
    prefix="/buildings",
    tags=["Buildings"],
)


@router.post(
    "",
    response_model=BuildingResponse,
)
def create_building(
    building_data: BuildingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "Super Admin",
            "Property Manager",
        )
    ),
):
    property_obj = db.query(Property).filter(
        Property.id == building_data.property_id
    ).first()

    if not property_obj:
        raise HTTPException(
            status_code=404,
            detail="Property not found",
        )

    building = Building(
        property_id=building_data.property_id,
        building_name=building_data.building_name,
        number_of_floors=building_data.number_of_floors,
        total_units=building_data.total_units,
    )

    db.add(building)
    db.commit()
    db.refresh(building)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="Building",
        entity_id=building.id,
        description=(
            f"Building '{building.building_name}' "
            f"was created."
        ),
    )

    return building


@router.get(
    "",
    response_model=list[BuildingResponse],
)
def get_buildings(
    property_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Building)

    if property_id is not None:
        query = query.filter(
            Building.property_id == property_id
        )

    return query.order_by(Building.id).all()