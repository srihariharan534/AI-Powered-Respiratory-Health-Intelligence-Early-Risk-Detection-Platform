"""
NEXUS Central FastAPI Application.
Offline-First Multi-Emergency Decision Intelligence Platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.app.routes import (
    hazards_router,
    hospitals_router,
    incidents_router,
    recommendations_router,
    risk_router,
    shelters_router,
    sms_router,
    sync_router,
)

app = FastAPI(
    title="NEXUS Emergency Decision Intelligence API",
    description="Multi-Emergency Decision Intelligence Platform backend connecting Digital Twin, GIS, AI Risk Models, and Offline Field Synchronization.",
    version="1.0.0",
)

# CORS middleware for Command Center & Field PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register central routers
app.include_router(hazards_router, prefix="/api/v1/hazards", tags=["Hazards"])
app.include_router(incidents_router, prefix="/api/v1/incidents", tags=["Incidents"])
app.include_router(hospitals_router, prefix="/api/v1/hospitals", tags=["Hospitals"])
app.include_router(shelters_router, prefix="/api/v1/shelters", tags=["Shelters"])
app.include_router(risk_router, prefix="/api/v1/risk", tags=["Risk Intelligence"])
app.include_router(recommendations_router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(sms_router, prefix="/api/v1/sms", tags=["SMS Fallback"])
app.include_router(sync_router, prefix="/api/v1/sync", tags=["Synchronization"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ONLINE",
        "service": "NEXUS Emergency Decision Intelligence Platform",
        "version": "1.0.0",
        "authority": "NEXUS-NODE-01",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "database": "CONNECTED",
        "digital_twin": "SYNCHRONIZED",
    }
