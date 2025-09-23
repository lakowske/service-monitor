"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from service_monitor.main import app, reset_storage
from service_monitor.models import ServiceStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    reset_storage()  # Reset storage before each test
    return TestClient(app)


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert "monitored_services" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert isinstance(data["monitored_services"], int)


def test_service_checkin_success(client):
    """Test successful service check-in."""
    checkin_data = {
        "service_name": "test-service",
        "status": "up",
        "message": "Service is running normally",
        "metadata": {"version": "1.0.0", "region": "us-west-2"}
    }

    response = client.post("/services/checkin", json=checkin_data)
    assert response.status_code == 201

    data = response.json()
    assert data["service_name"] == "test-service"
    assert data["status"] == "up"
    assert data["message"] == "Service is running normally"
    assert data["metadata"]["version"] == "1.0.0"
    assert data["check_in_count"] == 1
    assert "last_check_in" in data


def test_service_checkin_empty_name(client):
    """Test service check-in with empty service name."""
    checkin_data = {
        "service_name": "",
        "status": "up"
    }

    response = client.post("/services/checkin", json=checkin_data)
    assert response.status_code == 400
    assert "Service name cannot be empty" in response.json()["detail"]


def test_service_checkin_whitespace_name(client):
    """Test service check-in with whitespace-only service name."""
    checkin_data = {
        "service_name": "   ",
        "status": "up"
    }

    response = client.post("/services/checkin", json=checkin_data)
    assert response.status_code == 400


def test_multiple_checkins_same_service(client):
    """Test multiple check-ins for the same service."""
    checkin_data = {
        "service_name": "persistent-service",
        "status": "up"
    }

    # First check-in
    response1 = client.post("/services/checkin", json=checkin_data)
    assert response1.status_code == 201
    data1 = response1.json()
    assert data1["check_in_count"] == 1

    # Second check-in
    checkin_data["status"] = "degraded"
    checkin_data["message"] = "Performance issues detected"

    response2 = client.post("/services/checkin", json=checkin_data)
    assert response2.status_code == 201
    data2 = response2.json()
    assert data2["check_in_count"] == 2
    assert data2["status"] == "degraded"
    assert data2["message"] == "Performance issues detected"


def test_get_all_services_empty(client):
    """Test getting all services when none are registered."""
    response = client.get("/services")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_services_with_data(client):
    """Test getting all services after some check-ins."""
    # Add a few services
    services = [
        {"service_name": "service-1", "status": "up"},
        {"service_name": "service-2", "status": "down"},
        {"service_name": "service-3", "status": "degraded"}
    ]

    for service in services:
        client.post("/services/checkin", json=service)

    response = client.get("/services")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 3
    service_names = [s["service_name"] for s in data]
    assert "service-1" in service_names
    assert "service-2" in service_names
    assert "service-3" in service_names


def test_get_specific_service_success(client):
    """Test getting a specific service that exists."""
    # First, add a service
    checkin_data = {
        "service_name": "specific-service",
        "status": "up",
        "message": "Running well"
    }
    client.post("/services/checkin", json=checkin_data)

    # Then retrieve it
    response = client.get("/services/specific-service")
    assert response.status_code == 200

    data = response.json()
    assert data["service_name"] == "specific-service"
    assert data["status"] == "up"
    assert data["message"] == "Running well"


def test_get_specific_service_not_found(client):
    """Test getting a specific service that doesn't exist."""
    response = client.get("/services/nonexistent-service")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_remove_service_success(client):
    """Test removing a service that exists."""
    # First, add a service
    checkin_data = {"service_name": "removable-service", "status": "up"}
    client.post("/services/checkin", json=checkin_data)

    # Verify it exists
    response = client.get("/services/removable-service")
    assert response.status_code == 200

    # Remove it
    response = client.delete("/services/removable-service")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get("/services/removable-service")
    assert response.status_code == 404


def test_remove_service_not_found(client):
    """Test removing a service that doesn't exist."""
    response = client.delete("/services/nonexistent-service")
    assert response.status_code == 404


def test_get_services_by_status_valid(client):
    """Test filtering services by status."""
    # Add services with different statuses
    services = [
        {"service_name": "up-service-1", "status": "up"},
        {"service_name": "up-service-2", "status": "up"},
        {"service_name": "down-service", "status": "down"},
        {"service_name": "degraded-service", "status": "degraded"}
    ]

    for service in services:
        client.post("/services/checkin", json=service)

    # Test filtering by "up" status
    response = client.get("/services/status/up")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    for service in data:
        assert service["status"] == "up"

    # Test filtering by "down" status
    response = client.get("/services/status/down")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["service_name"] == "down-service"


def test_get_services_by_status_invalid(client):
    """Test filtering services by invalid status."""
    response = client.get("/services/status/invalid-status")
    assert response.status_code == 400
    assert "Invalid status filter" in response.json()["detail"]


def test_service_status_enum_values(client):
    """Test all valid service status enum values."""
    valid_statuses = ["up", "down", "degraded", "unknown"]

    for status in valid_statuses:
        checkin_data = {
            "service_name": f"service-{status}",
            "status": status
        }
        response = client.post("/services/checkin", json=checkin_data)
        assert response.status_code == 201
        assert response.json()["status"] == status


def test_invalid_service_status(client):
    """Test service check-in with invalid status."""
    checkin_data = {
        "service_name": "test-service",
        "status": "invalid-status"
    }

    response = client.post("/services/checkin", json=checkin_data)
    assert response.status_code == 422  # Pydantic validation error