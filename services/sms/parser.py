"""
Deterministic Emergency SMS Parser (Phase 26).
Parses standard format:
FLOOD <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
or
<EVENT_TYPE> <ENTITY_ID> <STATUS> <SEVERITY> <LAT> <LON>
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from services.sms.contracts import (
    SMSEventType,
    SMSMessage,
    SMSParseResult,
    SMSSeverity,
    SMSSource,
    SMSStatus,
)


class SMSParser:
    """
    Parses and strictly validates incoming compact SMS messages.
    Preserves raw string, validates coordinates, and enforces enum bounds.
    """

    @classmethod
    def parse(
        cls,
        raw_text: str,
        sender_reference: str = "ANON-SENDER-01",
        source: SMSSource = SMSSource.SIMULATED_SMS_DEMO,
        message_id: Optional[str] = None,
    ) -> SMSParseResult:
        if not raw_text or not raw_text.strip():
            return SMSParseResult(
                is_valid=False,
                raw_message=raw_text or "",
                error_message="SMS payload cannot be empty.",
            )

        trimmed = raw_text.strip()
        if len(trimmed) > 160:
            return SMSParseResult(
                is_valid=False,
                raw_message=trimmed,
                error_message="SMS length exceeds standard 160 character boundary.",
            )

        tokens = trimmed.split()
        if len(tokens) < 6:
            return SMSParseResult(
                is_valid=False,
                raw_message=trimmed,
                error_message=f"Insufficient SMS tokens. Expected 6 tokens, got {len(tokens)}.",
            )

        event_str, entity_id, status_str, severity_str, lat_str, lon_str = tokens[:6]
        field_errors = {}

        # 1. Event Type
        event_type = None
        try:
            event_type = SMSEventType(event_str.upper())
        except ValueError:
            field_errors["event_type"] = f"Invalid event_type '{event_str}'. Expected {[e.value for e in SMSEventType]}."

        # 2. Status
        status_val = None
        try:
            status_val = SMSStatus(status_str.upper())
        except ValueError:
            field_errors["status"] = f"Invalid status '{status_str}'. Expected {[s.value for s in SMSStatus]}."

        # 3. Severity
        severity_val = None
        try:
            severity_val = SMSSeverity(severity_str.upper())
        except ValueError:
            field_errors["severity"] = f"Invalid severity '{severity_str}'. Expected {[s.value for s in SMSSeverity]}."

        # 4. Latitude
        lat_val = None
        try:
            lat_val = float(lat_str)
            if not (-90.0 <= lat_val <= 90.0):
                field_errors["latitude"] = f"Latitude {lat_val} out of WGS84 range [-90.0, 90.0]."
        except ValueError:
            field_errors["latitude"] = f"Invalid float value for latitude: '{lat_str}'."

        # 5. Longitude
        lon_val = None
        try:
            lon_val = float(lon_str)
            if not (-180.0 <= lon_val <= 180.0):
                field_errors["longitude"] = f"Longitude {lon_val} out of WGS84 range [-180.0, 180.0]."
        except ValueError:
            field_errors["longitude"] = f"Invalid float value for longitude: '{lon_str}'."

        if field_errors:
            return SMSParseResult(
                is_valid=False,
                raw_message=trimmed,
                error_message="SMS validation failed on one or more fields.",
                field_errors=field_errors,
            )

        msg_id = message_id or f"SMS-{uuid.uuid4().hex[:8].upper()}"
        parsed_msg = SMSMessage(
            schema_version="1.0.0",
            message_id=msg_id,
            received_at=datetime.now(timezone.utc).isoformat(),
            sender_reference=sender_reference,
            raw_message=trimmed,
            event_type=event_type,
            entity_id=entity_id,
            status=status_val,
            severity=severity_val,
            latitude=lat_val,
            longitude=lon_val,
            source=source,
        )

        return SMSParseResult(
            is_valid=True,
            raw_message=trimmed,
            parsed_message=parsed_msg,
        )
