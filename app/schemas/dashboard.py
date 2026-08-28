from datetime import date

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_properties: int
    total_buildings: int
    total_units: int
    occupied_units: int
    available_units: int
    total_tenants: int
    active_leases: int
    monthly_rent_collection: float
    pending_rent: float
    overdue_rent: float
    maintenance_expenses: float
    utility_revenue: float
    parking_occupancy: float


class MonthlyRentCollectionResponse(BaseModel):
    billing_month: str
    total_collected: float
    payment_count: int


class PropertyRevenueResponse(BaseModel):
    property_id: int
    property_name: str
    total_revenue: float


class UnitOccupancyResponse(BaseModel):
    total_units: int
    occupied_units: int
    available_units: int
    reserved_units: int
    maintenance_units: int
    occupancy_percentage: float


class MaintenanceExpenseResponse(BaseModel):
    total_requests: int
    resolved_requests: int
    total_estimated_cost: float
    total_actual_cost: float


class UtilityConsumptionResponse(BaseModel):
    utility_type: str
    total_units_consumed: float
    total_revenue: float


class TenantPaymentHistoryResponse(BaseModel):
    tenant_id: int
    tenant_name: str
    total_paid: float
    payment_count: int


class LeaseExpiryResponse(BaseModel):
    lease_id: int
    tenant_id: int
    tenant_name: str
    unit_id: int
    end_date: date
    monthly_rent: float