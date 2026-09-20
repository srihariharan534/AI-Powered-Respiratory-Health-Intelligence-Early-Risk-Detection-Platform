"""
Canonical SMS Pydantic Contract.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

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
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0.0"] = "1.0.0"
    message_id: str = Field(..., min_length=3)
    received_at: datetime
    sender_reference: str
    raw_message: str = Field(..., max_length=160)
    event_type: SMSEventType
    entity_id: str
    status: SMSStatus
    severity: SMSSeverity
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    source: SMSSource
