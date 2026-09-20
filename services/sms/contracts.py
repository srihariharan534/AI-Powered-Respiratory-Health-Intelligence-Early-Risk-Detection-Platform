"""
Data Contracts for Structured Emergency SMS Fallback (Phase 26).
Conforms strictly to data/schemas/sms.schema.json.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class SMSEventType(str, Enum):
    FLOOD = "FLOOD"
    ROAD = "ROAD"
    BRIDGE = "BRIDGE"
    MEDICAL = "MEDICAL"
    SHELTER = "SHELTER"
    RESCUE = "RESCUE"


class SMSStatus(str, Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    FULL = "FULL"
    DAMAGED = "DAMAGED"
    CRITICAL = "CRITICAL"


class SMSSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SMSSource(str, Enum):
    SMS = "sms"
    SIMULATED_SMS_DEMO = "simulated_sms_demo"


class SMSMessage(BaseModel):
    """Canonical parsed and validated SMS contract."""
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0.0", description="Contract schema version")
    message_id: str = Field(..., min_length=3, description="Unique inbound SMS identifier")
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sender_reference: str = Field(..., description="Anonymized sender identifier")
    raw_message: str = Field(..., max_length=160, description="Exact 160-character inbound payload")
    event_type: SMSEventType
    entity_id: Optional[str] = Field(None, description="Referenced entity if present")
    status: SMSStatus
    severity: SMSSeverity
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    source: SMSSource = Field(default=SMSSource.SIMULATED_SMS_DEMO)


class SMSParseResult(BaseModel):
    """Outcome of SMS syntax parser."""
    is_valid: bool
    raw_message: str
    parsed_message: Optional[SMSMessage] = None
    error_message: Optional[str] = None
    field_errors: Dict[str, str] = Field(default_factory=dict)
