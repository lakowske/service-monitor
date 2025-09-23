"""Tests for the storage layer."""

import pytest
from datetime import datetime

from service_monitor.models import ServiceStatus
from service_monitor.storage import InMemoryStorage


@pytest.fixture
def storage():
    """Create a fresh storage instance for each test."""
    return InMemoryStorage()


def test_storage_initialization(storage):
    """Test storage initialization."""
    assert storage.get_service_count() == 0
    assert storage.get_all_services() == []


def test_update_new_service(storage):
    """Test updating a service that doesn't exist yet."""
    service = storage.update_service(
        service_name="new-service",
        status=ServiceStatus.UP,
        message="Initial startup",
        metadata={"version": "1.0.0"}
    )

    assert service.service_name == "new-service"
    assert service.status == ServiceStatus.UP
    assert service.message == "Initial startup"
    assert service.metadata["version"] == "1.0.0"
    assert service.check_in_count == 1
    assert isinstance(service.last_check_in, datetime)


def test_update_existing_service(storage):
    """Test updating a service that already exists."""
    # First check-in
    service1 = storage.update_service(
        service_name="existing-service",
        status=ServiceStatus.UP,
        message="First check-in"
    )
    first_checkin_time = service1.last_check_in

    # Second check-in
    service2 = storage.update_service(
        service_name="existing-service",
        status=ServiceStatus.DEGRADED,
        message="Performance issues",
        metadata={"load": "high"}
    )

    assert service2.service_name == "existing-service"
    assert service2.status == ServiceStatus.DEGRADED
    assert service2.message == "Performance issues"
    assert service2.metadata["load"] == "high"
    assert service2.check_in_count == 2
    assert service2.last_check_in > first_checkin_time


def test_update_service_metadata_merge(storage):
    """Test that metadata is merged on subsequent updates."""
    # First check-in with initial metadata
    storage.update_service(
        service_name="metadata-service",
        status=ServiceStatus.UP,
        metadata={"version": "1.0.0", "region": "us-west"}
    )

    # Second check-in with additional metadata
    service = storage.update_service(
        service_name="metadata-service",
        status=ServiceStatus.UP,
        metadata={"load": "low", "region": "us-east"}  # region should be updated
    )

    assert service.metadata["version"] == "1.0.0"  # preserved
    assert service.metadata["region"] == "us-east"  # updated
    assert service.metadata["load"] == "low"  # added


def test_get_service_existing(storage):
    """Test getting a service that exists."""
    # Add a service
    storage.update_service("test-service", ServiceStatus.UP, "Running well")

    # Retrieve it
    service = storage.get_service("test-service")
    assert service is not None
    assert service.service_name == "test-service"
    assert service.status == ServiceStatus.UP


def test_get_service_nonexistent(storage):
    """Test getting a service that doesn't exist."""
    service = storage.get_service("nonexistent-service")
    assert service is None


def test_get_all_services(storage):
    """Test getting all services."""
    # Add multiple services
    services_data = [
        ("service-1", ServiceStatus.UP),
        ("service-2", ServiceStatus.DOWN),
        ("service-3", ServiceStatus.DEGRADED)
    ]

    for name, status in services_data:
        storage.update_service(name, status)

    # Get all services
    all_services = storage.get_all_services()
    assert len(all_services) == 3

    service_names = [s.service_name for s in all_services]
    assert "service-1" in service_names
    assert "service-2" in service_names
    assert "service-3" in service_names


def test_remove_service_existing(storage):
    """Test removing a service that exists."""
    # Add a service
    storage.update_service("removable-service", ServiceStatus.UP)
    assert storage.get_service_count() == 1

    # Remove it
    result = storage.remove_service("removable-service")
    assert result is True
    assert storage.get_service_count() == 0
    assert storage.get_service("removable-service") is None


def test_remove_service_nonexistent(storage):
    """Test removing a service that doesn't exist."""
    result = storage.remove_service("nonexistent-service")
    assert result is False


def test_get_services_by_status(storage):
    """Test filtering services by status."""
    # Add services with different statuses
    services_data = [
        ("up-service-1", ServiceStatus.UP),
        ("up-service-2", ServiceStatus.UP),
        ("down-service", ServiceStatus.DOWN),
        ("degraded-service", ServiceStatus.DEGRADED),
        ("unknown-service", ServiceStatus.UNKNOWN)
    ]

    for name, status in services_data:
        storage.update_service(name, status)

    # Test filtering by UP status
    up_services = storage.get_services_by_status(ServiceStatus.UP)
    assert len(up_services) == 2
    for service in up_services:
        assert service.status == ServiceStatus.UP

    # Test filtering by DOWN status
    down_services = storage.get_services_by_status(ServiceStatus.DOWN)
    assert len(down_services) == 1
    assert down_services[0].service_name == "down-service"

    # Test filtering by status with no matches
    # First remove all services and add only non-UP services
    for name, _ in services_data:
        storage.remove_service(name)

    storage.update_service("test-down", ServiceStatus.DOWN)
    up_services = storage.get_services_by_status(ServiceStatus.UP)
    assert len(up_services) == 0


def test_get_service_count(storage):
    """Test getting the service count."""
    assert storage.get_service_count() == 0

    # Add some services
    storage.update_service("service-1", ServiceStatus.UP)
    assert storage.get_service_count() == 1

    storage.update_service("service-2", ServiceStatus.DOWN)
    assert storage.get_service_count() == 2

    # Update existing service shouldn't change count
    storage.update_service("service-1", ServiceStatus.DEGRADED)
    assert storage.get_service_count() == 2

    # Remove a service
    storage.remove_service("service-1")
    assert storage.get_service_count() == 1


def test_service_none_metadata(storage):
    """Test service update with None metadata."""
    service = storage.update_service(
        service_name="no-metadata-service",
        status=ServiceStatus.UP,
        metadata=None
    )

    assert service.metadata == {}


def test_service_empty_metadata(storage):
    """Test service update with empty metadata."""
    service = storage.update_service(
        service_name="empty-metadata-service",
        status=ServiceStatus.UP,
        metadata={}
    )

    assert service.metadata == {}