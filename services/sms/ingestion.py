"""
SMS Ingestion Service and Dual-Mode Provider Abstraction (Phase 26).
Ensures raw-message preservation, duplicate/replay protection, and Digital Twin event propagation.
"""

import hashlib
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from digital_twin.events.base import EventSource
from digital_twin.events.incident_created import IncidentCreatedEvent
from digital_twin.state.state_manager import DigitalTwinStateManager
from services.api.app.repositories.incident_service import IncidentService
from services.api.app.schemas.incident import (
    Incident,
    IncidentEventType,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
    PointLocation,
)
from services.sms.contracts import (
    SMSEventType,
    SMSMessage,
    SMSParseResult,
    SMSSource,
)
from services.sms.parser import SMSParser


class SMSIngestionResult:
    def __init__(
        self,
        success: bool,
        message_id: str,
        status: str,
        error: Optional[str] = None,
        incident_id: Optional[str] = None,
        raw_message: Optional[str] = None,
        is_duplicate: bool = False,
    ):
        self.success = success
        self.message_id = message_id
        self.status = status
        self.error = error
        self.incident_id = incident_id
        self.raw_message = raw_message
        self.is_duplicate = is_duplicate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "status": self.status,
            "error": self.error,
            "incident_id": self.incident_id,
            "raw_message": self.raw_message,
            "is_duplicate": self.is_duplicate,
        }


class SMSIngestionService:
    """
    Central SMS ingestion engine.
    - Preserves all raw inbound payloads in an append-only archive.
    - Applies deduplication and replay protection via payload SHA-256 hashes.
    - Propagates valid operational messages into the IncidentService and Digital Twin.
    """

    def __init__(
        self,
        incident_service: Optional[IncidentService] = None,
        digital_twin: Optional[DigitalTwinStateManager] = None,
    ) -> None:
        self.digital_twin = digital_twin or DigitalTwinStateManager()
        self.incident_service = incident_service or IncidentService(digital_twin=self.digital_twin)
        self._lock = threading.Lock()
        self._raw_inbound_archive: List[Dict[str, Any]] = []
        self._seen_message_hashes: Dict[str, str] = {}  # hash -> message_id

    def ingest_sms(
        self,
        raw_text: str,
        sender_reference: str = "ANON-TELECOM-REPLY",
        source: SMSSource = SMSSource.SIMULATED_SMS_DEMO,
    ) -> SMSIngestionResult:
        with self._lock:
            # 1. Record raw message in immutable archive
            raw_entry = {
                "archive_id": f"RAW-{uuid.uuid4().hex[:8]}",
                "raw_text": raw_text,
                "sender_reference": sender_reference,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "source": source.value,
            }
            self._raw_inbound_archive.append(raw_entry)

            # 2. Replay & Duplicate Check
            msg_hash = hashlib.sha256(raw_text.strip().encode("utf-8")).hexdigest()
            if msg_hash in self._seen_message_hashes:
                existing_msg_id = self._seen_message_hashes[msg_hash]
                return SMSIngestionResult(
                    success=True,
                    message_id=existing_msg_id,
                    status="DUPLICATE_REJECTED",
                    error="Duplicate SMS detected. Replay rejected to protect state integrity.",
                    raw_message=raw_text,
                    is_duplicate=True,
                )

            # 3. Parse and Validate Syntax
            parse_result = SMSParser.parse(
                raw_text=raw_text,
                sender_reference=sender_reference,
                source=source,
            )

            if not parse_result.is_valid or not parse_result.parsed_message:
                return SMSIngestionResult(
                    success=False,
                    message_id="INVALID",
                    status="PARSE_ERROR",
                    error=parse_result.error_message or "Unknown parse error",
                    raw_message=raw_text,
                )

            msg = parse_result.parsed_message
            self._seen_message_hashes[msg_hash] = msg.message_id

            # 4. Map to Canonical Incident Model
            # Map SMS severity to Incident severity
            sev_mapping = {
                "LOW": IncidentSeverity.LOW,
                "MEDIUM": IncidentSeverity.MEDIUM,
                "HIGH": IncidentSeverity.HIGH,
                "CRITICAL": IncidentSeverity.CRITICAL,
            }
            event_mapping = {
                SMSEventType.FLOOD: IncidentEventType.FLOOD_INUNDATION,
                SMSEventType.ROAD: IncidentEventType.ROAD_BLOCKED,
                SMSEventType.BRIDGE: IncidentEventType.BRIDGE_FAILURE,
                SMSEventType.MEDICAL: IncidentEventType.MEDICAL_EMERGENCY,
                SMSEventType.SHELTER: IncidentEventType.SHELTER_NEEDED,
                SMSEventType.RESCUE: IncidentEventType.TRAPPED_PERSONS,
            }

            canonical_incident_id = f"INC-SMS-{uuid.uuid4().hex[:6].upper()}"
            incident = Incident(
                schema_version="1.0.0",
                incident_id=canonical_incident_id,
                event_type=event_mapping.get(msg.event_type, IncidentEventType.FLOOD_INUNDATION),
                severity=sev_mapping.get(msg.severity.value, IncidentSeverity.MEDIUM),
                status=IncidentStatus.OPEN,
                priority=1 if msg.severity.value == "CRITICAL" else 2,
                location=PointLocation(type="Point", coordinates=[msg.longitude, msg.latitude]),
                reported_at=datetime.now(timezone.utc).isoformat(),
                reported_by=msg.sender_reference,
                description=f"[SMS FALLBACK] Entity: {msg.entity_id or 'UNKNOWN'}, Status: {msg.status.value}. Raw: {msg.raw_message}",
                source=IncidentSource.SMS if source == SMSSource.SMS else IncidentSource.SYNTHETIC_DEMO,
            )

            try:
                self.incident_service.create_incident(incident, actor=f"SMS_GATEWAY_{source.value}")
                return SMSIngestionResult(
                    success=True,
                    message_id=msg.message_id,
                    status="INGESTED",
                    incident_id=canonical_incident_id,
                    raw_message=raw_text,
                )
            except Exception as err:
                return SMSIngestionResult(
                    success=False,
                    message_id=msg.message_id,
                    status="DOMAIN_REJECTED",
                    error=str(err),
                    raw_message=raw_text,
                )

    def get_archive(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._raw_inbound_archive)
