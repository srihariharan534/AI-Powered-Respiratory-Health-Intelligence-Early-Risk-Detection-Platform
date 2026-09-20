"""
NEXUS API Routes Package.
Exports API routers for hospitals, shelters, incidents, and risk intelligence.
"""

from services.api.app.routes.hazards import router as hazards_router
from services.api.app.routes.hospitals import router as hospitals_router
from services.api.app.routes.incidents import router as incidents_router
from services.api.app.routes.recommendations import router as recommendations_router
from services.api.app.routes.risk import router as risk_router
from services.api.app.routes.shelters import router as shelters_router
from services.api.app.routes.sms import router as sms_router
from services.api.app.routes.sync import router as sync_router

__all__ = [
    "hazards_router",
    "hospitals_router",
    "incidents_router",
    "recommendations_router",
    "shelters_router",
    "risk_router",
    "sync_router",
    "sms_router",
]




