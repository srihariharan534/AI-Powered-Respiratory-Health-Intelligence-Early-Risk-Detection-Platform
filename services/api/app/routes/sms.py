"""
SMS Fallback Gateway Ingestion REST API Endpoints (Phase 26).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.recommendations.governance.roles import AuthenticatedActor, get_current_actor
from services.sms.contracts import SMSSource
from services.sms.ingestion import SMSIngestionService

router = APIRouter(prefix="/api/v1/sms", tags=["SMS Fallback Ingestion"])

_sms_service = SMSIngestionService()


def get_sms_service() -> SMSIngestionService:
    return _sms_service


class SMSIngestRequest(BaseModel):
    raw_message: str = Field(..., max_length=160, description="Raw 160-character compact SMS text")
    sender_reference: str = Field(default="ANON-RADIO-01", description="Anonymized radio/phone reference")
    simulated: bool = Field(default=True, description="Flag indicating simulated SMS demo mode")


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_emergency_sms(
    request: SMSIngestRequest,
    service: SMSIngestionService = Depends(get_sms_service),
) -> Dict[str, Any]:
    """
    Ingest, validate, and normalize compact SMS reports into authoritative incident state.
    """
    source = SMSSource.SIMULATED_SMS_DEMO if request.simulated else SMSSource.SMS
    result = service.ingest_sms(
        raw_text=request.raw_message,
        sender_reference=request.sender_reference,
        source=source,
    )
    if not result.success and result.status == "PARSE_ERROR":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PARSE_ERROR", "message": result.error, "raw": result.raw_message},
        )
    return result.to_dict()


@router.get("/archive", response_model=List[Dict[str, Any]])
def get_raw_sms_archive(
    service: SMSIngestionService = Depends(get_sms_service),
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> List[Dict[str, Any]]:
    """
    Inspect raw inbound SMS archive for auditability.
    """
    return service.get_archive()
