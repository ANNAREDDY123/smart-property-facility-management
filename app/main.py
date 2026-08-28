from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.rate_limit import limiter

from app.routes.auth import router as auth_router
from app.routes.property import router as property_router
from app.routes.building import router as building_router
from app.routes.unit import router as unit_router
from app.routes.tenant import router as tenant_router
from app.routes.lease import router as lease_router
from app.routes.rent_invoice import router as rent_invoice_router
from app.routes.payment import router as payment_router
from app.routes.maintenance import router as maintenance_router
from app.routes.rent import router as rent_router
from app.routes.visitor import router as visitor_router
from app.routes.utility import router as utility_router
from app.routes.parking import router as parking_router
from app.routes.facility import router as facility_router
from app.routes.dashboard import router as dashboard_router
from app.routes.notification import router as notification_router
from app.routes.audit import router as audit_router
from app.routes.audit_log import router as audit_log_router
from app.routes.maintenance_request import (
    router as maintenance_request_router,
)
from app.routes.work_order import (
    router as work_order_router,
)


app = FastAPI(
    title="Smart Property & Facility Management Platform",
    version="1.0.0",
    description="Property and facility management backend built with FastAPI.",
)



# RATE LIMITING

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)



# CORS CONFIGURATION

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ROUTES


app.include_router(auth_router)
app.include_router(property_router)
app.include_router(building_router)
app.include_router(unit_router)
app.include_router(tenant_router)
app.include_router(lease_router)
app.include_router(rent_invoice_router)
app.include_router(payment_router)
app.include_router(rent_router)
app.include_router(maintenance_request_router)
app.include_router(maintenance_router)
app.include_router(work_order_router)
app.include_router(utility_router)
app.include_router(visitor_router)
app.include_router(parking_router)
app.include_router(facility_router)
app.include_router(notification_router)
app.include_router(dashboard_router)
app.include_router(audit_router)
app.include_router(audit_log_router)



# ROOT ENDPOINT

@app.get("/")
def root():
    return {
        "message": "Smart Property & Facility Management API is running"
    }