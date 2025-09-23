"""Tests for the data models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from service_monitor.models import HealthResponse, ServiceCheckIn, ServiceInfo, ServiceStatus


def test_service_status_enum():
    """Test ServiceStatus enum values."""
    assert ServiceStatus.UP == "up"
    assert ServiceStatus.DOWN == "down"
    assert ServiceStatus.DEGRADED == "degraded"
    assert ServiceStatus.UNKNOWN == "unknown"


def test_service_checkin_valid():
    """Test valid ServiceCheckIn creation."""
    checkin = ServiceCheckIn(
        service_name="test-service",
        status=ServiceStatus.UP,
        message="Service is running",
        metadata={"version": "1.0.0", "region": "us-west"},
    )

    assert checkin.service_name == "test-service"
    assert checkin.status == ServiceStatus.UP
    assert checkin.message == "Service is running"
    assert checkin.metadata["version"] == "1.0.0"
    assert checkin.metadata["region"] == "us-west"


def test_service_checkin_minimal():
    """Test ServiceCheckIn with minimal required fields."""
    checkin = ServiceCheckIn(service_name="minimal-service", status=ServiceStatus.DOWN)

    assert checkin.service_name == "minimal-service"
    assert checkin.status == ServiceStatus.DOWN
    assert checkin.message is None
    assert checkin.metadata == {}


def test_service_checkin_invalid_status():
    """Test ServiceCheckIn with invalid status."""
    with pytest.raises(ValidationError) as exc_info:
        ServiceCheckIn(service_name="test-service", status="invalid-status")

    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "status" in errors[0]["loc"]


def test_service_checkin_empty_service_name():
    """Test ServiceCheckIn allows empty service name (validation happens at API level)."""
    checkin = ServiceCheckIn(service_name="", status=ServiceStatus.UP)
    assert checkin.service_name == ""


def test_service_info_creation():
    """Test ServiceInfo creation."""
    timestamp = datetime.now(timezone.utc)
    service = ServiceInfo(
        service_name="info-service",
        status=ServiceStatus.DEGRADED,
        last_check_in=timestamp,
        message="Performance issues",
        metadata={"load": "high"},
        check_in_count=5,
    )

    assert service.service_name == "info-service"
    assert service.status == ServiceStatus.DEGRADED
    assert service.last_check_in == timestamp
    assert service.message == "Performance issues"
    assert service.metadata["load"] == "high"
    assert service.check_in_count == 5


def test_service_info_defaults():
    """Test ServiceInfo with default values."""
    timestamp = datetime.now(timezone.utc)
    service = ServiceInfo(service_name="default-service", status=ServiceStatus.UP, last_check_in=timestamp)

    assert service.service_name == "default-service"
    assert service.status == ServiceStatus.UP
    assert service.last_check_in == timestamp
    assert service.message is None
    assert service.metadata == {}
    assert service.check_in_count == 0


def test_health_response_creation():
    """Test HealthResponse creation."""
    timestamp = datetime.now(timezone.utc)
    health = HealthResponse(status="healthy", timestamp=timestamp, uptime_seconds=123.45, monitored_services=10)

    assert health.status == "healthy"
    assert health.timestamp == timestamp
    assert health.uptime_seconds == 123.45
    assert health.monitored_services == 10


def test_health_response_validation():
    """Test HealthResponse field validation."""
    timestamp = datetime.now(timezone.utc)

    # Test with negative uptime (should be allowed)
    health = HealthResponse(status="healthy", timestamp=timestamp, uptime_seconds=-1.0, monitored_services=0)
    assert health.uptime_seconds == -1.0

    # Test with negative monitored services (should be allowed)
    health = HealthResponse(status="unhealthy", timestamp=timestamp, uptime_seconds=100.0, monitored_services=-1)
    assert health.monitored_services == -1


def test_service_checkin_json_serialization():
    """Test ServiceCheckIn JSON serialization."""
    checkin = ServiceCheckIn(
        service_name="json-service", status=ServiceStatus.UP, message="All good", metadata={"key": "value"}
    )

    json_data = checkin.model_dump()
    assert json_data["service_name"] == "json-service"
    assert json_data["status"] == "up"
    assert json_data["message"] == "All good"
    assert json_data["metadata"]["key"] == "value"


def test_service_info_json_serialization():
    """Test ServiceInfo JSON serialization."""
    timestamp = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    service = ServiceInfo(
        service_name="json-info-service",
        status=ServiceStatus.DOWN,
        last_check_in=timestamp,
        message="Service offline",
        metadata={"reason": "maintenance"},
        check_in_count=3,
    )

    json_data = service.model_dump()
    assert json_data["service_name"] == "json-info-service"
    assert json_data["status"] == "down"
    assert json_data["message"] == "Service offline"
    assert json_data["metadata"]["reason"] == "maintenance"
    assert json_data["check_in_count"] == 3


def test_all_service_status_values():
    """Test that all ServiceStatus values work in ServiceCheckIn."""
    for status in ServiceStatus:
        checkin = ServiceCheckIn(service_name=f"service-{status.value}", status=status)
        assert checkin.status == status


def test_metadata_type_validation():
    """Test metadata field type validation."""
    # Valid metadata (Dict[str, str])
    checkin = ServiceCheckIn(
        service_name="metadata-service", status=ServiceStatus.UP, metadata={"key1": "value1", "key2": "value2"}
    )
    assert isinstance(checkin.metadata, dict)

    # Test with non-string values (should be converted or cause validation error)
    with pytest.raises(ValidationError):
        ServiceCheckIn(
            service_name="invalid-metadata-service",
            status=ServiceStatus.UP,
            metadata={"key1": 123, "key2": True},  # Non-string values
        )
