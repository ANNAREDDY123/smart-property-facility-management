from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.building import Building
from app.models.lease import Lease
from app.models.maintenance_request import MaintenanceRequest
from app.models.parking import Parking
from app.models.payment import Payment
from app.models.property import Property
from app.models.rent_invoice import RentInvoice
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.models.utility_invoice import UtilityInvoice
from app.utils.dependencies import get_current_user, require_roles
from app.models.user import User

from app.schemas.dashboard import (
    DashboardResponse,
    LeaseExpiryResponse,
    MaintenanceExpenseResponse,
    MonthlyRentCollectionResponse,
    PropertyRevenueResponse,
    TenantPaymentHistoryResponse,
    UnitOccupancyResponse,
    UtilityConsumptionResponse,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


DASHBOARD_ROLES = (
    "Super Admin",
    "Property Manager",
    "Facility Manager",
)


def validate_billing_month(
    billing_month: str,
) -> None:
    if (
        len(billing_month) != 7
        or billing_month[4] != "-"
    ):
        raise HTTPException(
            status_code=400,
            detail="billing_month must be in YYYY-MM format",
        )

    year, month = billing_month.split("-")

    if not year.isdigit() or not month.isdigit():
        raise HTTPException(
            status_code=400,
            detail="billing_month must be in YYYY-MM format",
        )

    month_number = int(month)

    if month_number < 1 or month_number > 12:
        raise HTTPException(
            status_code=400,
            detail="billing_month must be in YYYY-MM format",
        )


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    billing_month: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    if billing_month is not None:
        validate_billing_month(billing_month)

    total_properties = db.query(
        func.count(Property.id)
    ).scalar() or 0

    total_buildings = db.query(
        func.count(Building.id)
    ).scalar() or 0

    total_units = db.query(
        func.count(Unit.id)
    ).scalar() or 0

    occupied_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Occupied"
    ).scalar() or 0

    available_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Available"
    ).scalar() or 0

    total_tenants = db.query(
        func.count(Tenant.id)
    ).scalar() or 0

    active_leases = db.query(
        func.count(Lease.id)
    ).filter(
        Lease.lease_status == "Active"
    ).scalar() or 0

    rent_query = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0,
        )
    ).join(
        RentInvoice,
        RentInvoice.id == Payment.invoice_id,
    ).filter(
        Payment.payment_status == "Success"
    )

    if billing_month is not None:
        rent_query = rent_query.filter(
            RentInvoice.billing_month
            == billing_month
        )

    monthly_rent_collection = (
        rent_query.scalar() or 0
    )

    pending_query = db.query(
        func.coalesce(
            func.sum(RentInvoice.total_amount),
            0,
        )
    ).filter(
        RentInvoice.status == "Pending"
    )

    if billing_month is not None:
        pending_query = pending_query.filter(
            RentInvoice.billing_month
            == billing_month
        )

    pending_rent = (
        pending_query.scalar() or 0
    )

    overdue_query = db.query(
        func.coalesce(
            func.sum(RentInvoice.total_amount),
            0,
        )
    ).filter(
        RentInvoice.status == "Overdue"
    )

    if billing_month is not None:
        overdue_query = overdue_query.filter(
            RentInvoice.billing_month
            == billing_month
        )

    overdue_rent = (
        overdue_query.scalar() or 0
    )

    maintenance_expenses = db.query(
        func.coalesce(
            func.sum(
                MaintenanceRequest.actual_cost
            ),
            0,
        )
    ).scalar() or 0

    utility_query = db.query(
        func.coalesce(
            func.sum(
                UtilityInvoice.total_amount
            ),
            0,
        )
    )

    if billing_month is not None:
        utility_query = utility_query.filter(
            UtilityInvoice.billing_month
            == billing_month
        )

    utility_revenue = (
        utility_query.scalar() or 0
    )

    total_parking = db.query(
        func.count(Parking.id)
    ).scalar() or 0

    assigned_parking = db.query(
        func.count(Parking.id)
    ).filter(
        Parking.status == "Assigned"
    ).scalar() or 0

    if total_parking > 0:
        parking_occupancy = (
            assigned_parking
            / total_parking
        ) * 100
    else:
        parking_occupancy = 0.0

    return {
        "total_properties": total_properties,
        "total_buildings": total_buildings,
        "total_units": total_units,
        "occupied_units": occupied_units,
        "available_units": available_units,
        "total_tenants": total_tenants,
        "active_leases": active_leases,
        "monthly_rent_collection": float(
            monthly_rent_collection
        ),
        "pending_rent": float(
            pending_rent
        ),
        "overdue_rent": float(
            overdue_rent
        ),
        "maintenance_expenses": float(
            maintenance_expenses
        ),
        "utility_revenue": float(
            utility_revenue
        ),
        "parking_occupancy": float(
            parking_occupancy
        ),
    }


@router.get(
    "/reports/rent-collection",
    response_model=MonthlyRentCollectionResponse,
)
def rent_collection_report(
    billing_month: str = Query(
        ...,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    validate_billing_month(billing_month)

    result = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0,
        ),
        func.count(Payment.id),
    ).join(
        RentInvoice,
        RentInvoice.id == Payment.invoice_id,
    ).filter(
        RentInvoice.billing_month
        == billing_month,
        Payment.payment_status == "Success",
    ).first()

    return {
        "billing_month": billing_month,
        "total_collected": float(
            result[0] or 0
        ),
        "payment_count": result[1] or 0,
    }


@router.get(
    "/reports/property-revenue",
    response_model=list[PropertyRevenueResponse],
)
def property_revenue_report(
    billing_month: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    if billing_month is not None:
        validate_billing_month(billing_month)

    query = db.query(
        Property.id.label("property_id"),
        Property.property_name.label(
            "property_name"
        ),
        func.coalesce(
            func.sum(Payment.amount),
            0,
        ).label("total_revenue"),
    ).join(
        Building,
        Building.property_id == Property.id,
    ).join(
        Unit,
        Unit.building_id == Building.id,
    ).join(
        Lease,
        Lease.unit_id == Unit.id,
    ).join(
        RentInvoice,
        RentInvoice.lease_id == Lease.id,
    ).join(
        Payment,
        Payment.invoice_id == RentInvoice.id,
    ).filter(
        Payment.payment_status == "Success",
    )

    if billing_month is not None:
        query = query.filter(
            RentInvoice.billing_month
            == billing_month
        )

    results = query.group_by(
        Property.id,
        Property.property_name,
    ).order_by(
        Property.id
    ).all()

    return [
        {
            "property_id": row.property_id,
            "property_name": row.property_name,
            "total_revenue": float(
                row.total_revenue or 0
            ),
        }
        for row in results
    ]


@router.get(
    "/reports/unit-occupancy",
    response_model=UnitOccupancyResponse,
)
def unit_occupancy_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    total_units = db.query(
        func.count(Unit.id)
    ).scalar() or 0

    occupied_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Occupied"
    ).scalar() or 0

    available_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Available"
    ).scalar() or 0

    reserved_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Reserved"
    ).scalar() or 0

    maintenance_units = db.query(
        func.count(Unit.id)
    ).filter(
        Unit.status == "Maintenance"
    ).scalar() or 0

    occupancy_percentage = (
        occupied_units / total_units * 100
        if total_units > 0
        else 0.0
    )

    return {
        "total_units": total_units,
        "occupied_units": occupied_units,
        "available_units": available_units,
        "reserved_units": reserved_units,
        "maintenance_units": maintenance_units,
        "occupancy_percentage": float(
            occupancy_percentage
        ),
    }


@router.get(
    "/reports/maintenance-expenses",
    response_model=MaintenanceExpenseResponse,
)
def maintenance_expense_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    total_requests = db.query(
        func.count(
            MaintenanceRequest.id
        )
    ).scalar() or 0

    resolved_requests = db.query(
        func.count(
            MaintenanceRequest.id
        )
    ).filter(
        MaintenanceRequest.status == "Resolved"
    ).scalar() or 0

    total_estimated_cost = db.query(
        func.coalesce(
            func.sum(
                MaintenanceRequest.estimated_cost
            ),
            0,
        )
    ).scalar() or 0

    total_actual_cost = db.query(
        func.coalesce(
            func.sum(
                MaintenanceRequest.actual_cost
            ),
            0,
        )
    ).scalar() or 0

    return {
        "total_requests": total_requests,
        "resolved_requests": resolved_requests,
        "total_estimated_cost": float(
            total_estimated_cost
        ),
        "total_actual_cost": float(
            total_actual_cost
        ),
    }


@router.get(
    "/reports/utility-consumption",
    response_model=list[UtilityConsumptionResponse],
)
def utility_consumption_report(
    billing_month: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    if billing_month is not None:
        validate_billing_month(billing_month)

    query = db.query(
        UtilityInvoice.utility_type.label(
            "utility_type"
        ),
        func.coalesce(
            func.sum(
                UtilityInvoice.units_consumed
            ),
            0,
        ).label("total_units_consumed"),
        func.coalesce(
            func.sum(
                UtilityInvoice.total_amount
            ),
            0,
        ).label("total_revenue"),
    )

    if billing_month is not None:
        query = query.filter(
            UtilityInvoice.billing_month
            == billing_month
        )

    results = query.group_by(
        UtilityInvoice.utility_type
    ).order_by(
        UtilityInvoice.utility_type
    ).all()

    return [
        {
            "utility_type": row.utility_type,
            "total_units_consumed": float(
                row.total_units_consumed or 0
            ),
            "total_revenue": float(
                row.total_revenue or 0
            ),
        }
        for row in results
    ]


@router.get(
    "/reports/tenant-payment-history",
    response_model=list[TenantPaymentHistoryResponse],
)
def tenant_payment_history_report(
    tenant_id: int | None = None,
    billing_month: str | None = Query(
        default=None,
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    if billing_month is not None:
        validate_billing_month(billing_month)

    query = db.query(
        Tenant.id.label("tenant_id"),
        Tenant.full_name.label("tenant_name"),
        func.coalesce(
            func.sum(Payment.amount),
            0,
        ).label("total_paid"),
        func.count(
            Payment.id
        ).label("payment_count"),
    ).join(
        Lease,
        Lease.tenant_id == Tenant.id,
    ).join(
        RentInvoice,
        RentInvoice.lease_id == Lease.id,
    ).join(
        Payment,
        Payment.invoice_id == RentInvoice.id,
    ).filter(
        Payment.payment_status == "Success",
    )

    if tenant_id is not None:
        query = query.filter(
            Tenant.id == tenant_id
        )

    if billing_month is not None:
        query = query.filter(
            RentInvoice.billing_month
            == billing_month
        )

    results = query.group_by(
        Tenant.id,
        Tenant.full_name,
    ).order_by(
        Tenant.id
    ).all()

    return [
        {
            "tenant_id": row.tenant_id,
            "tenant_name": row.tenant_name,
            "total_paid": float(
                row.total_paid or 0
            ),
            "payment_count": row.payment_count or 0,
        }
        for row in results
    ]


@router.get(
    "/reports/lease-expiry",
    response_model=list[LeaseExpiryResponse],
)
def lease_expiry_report(
    before_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*DASHBOARD_ROLES)
    ),
):
    query = db.query(
        Lease,
        Tenant.full_name.label(
            "tenant_name"
        ),
    ).join(
        Tenant,
        Tenant.id == Lease.tenant_id,
    ).filter(
        Lease.lease_status == "Active",
    )

    if before_date is not None:
        query = query.filter(
            Lease.end_date <= before_date
        )

    results = query.order_by(
        Lease.end_date
    ).all()

    return [
        {
            "lease_id": lease.id,
            "tenant_id": lease.tenant_id,
            "tenant_name": tenant_name,
            "unit_id": lease.unit_id,
            "end_date": lease.end_date,
            "monthly_rent": float(
                lease.monthly_rent
            ),
        }
        for lease, tenant_name in results
    ]