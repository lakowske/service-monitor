"""Data models for the service monitor application."""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Enumeration of possible service statuses."""

    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ServiceCheckIn(BaseModel):
    """Model for service check-in requests."""

    service_name: str = Field(..., description="Name of the service checking in")
    status: ServiceStatus = Field(..., description="Current status of the service")
    message: Optional[str] = Field(None, description="Optional status message")
    metadata: Optional[dict[str, str]] = Field(default_factory=dict, description="Additional metadata")


class ServiceInfo(BaseModel):
    """Model representing the current state of a monitored service."""

    service_name: str = Field(..., description="Name of the service")
    status: ServiceStatus = Field(..., description="Current status of the service")
    last_check_in: datetime = Field(..., description="Timestamp of last check-in")
    message: Optional[str] = Field(None, description="Last status message")
    metadata: Optional[dict[str, str]] = Field(default_factory=dict, description="Service metadata")
    check_in_count: int = Field(default=0, description="Total number of check-ins")


class HealthResponse(BaseModel):
    """Model for health check responses."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Response timestamp")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    monitored_services: int = Field(..., description="Number of services being monitored")
