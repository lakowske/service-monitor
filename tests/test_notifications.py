"""Tests for the notification system."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from service_monitor.models import ServiceInfo, ServiceStatus
from service_monitor.notifications import EmailNotificationService, NotificationHistory


@pytest.fixture
def service_info():
    """Create a test service info."""
    return ServiceInfo(
        service_name="test-service",
        status=ServiceStatus.DOWN,
        last_check_in=datetime.now(timezone.utc),
        message="Test service is down",
        metadata={"version": "1.0.0"},
        check_in_count=1,
    )


@pytest.fixture
def notification_service():
    """Create a notification service instance."""
    with patch("service_monitor.config.config") as mock_config:
        mock_config.notifications.enabled = True
        mock_config.notifications.recipients = ["test@example.com"]
        mock_config.notifications.cooldown_minutes = 60
        service = EmailNotificationService()
        yield service


def test_notification_service_init(notification_service):
    """Test notification service initialization."""
    assert notification_service._notification_history == {}
    assert notification_service._client is not None


def test_should_send_notification_disabled():
    """Test that notifications are not sent when disabled."""
    with patch("service_monitor.notifications.config") as mock_config:
        mock_config.notifications.enabled = False
        service = EmailNotificationService()

        test_service = ServiceInfo(
            service_name="test",
            status=ServiceStatus.DOWN,
            last_check_in=datetime.now(timezone.utc),
            check_in_count=1,
        )

        assert not service._should_send_notification(test_service)


def test_should_send_notification_for_down_service(notification_service, service_info):
    """Test that notifications are sent for DOWN services."""
    assert notification_service._should_send_notification(service_info)


def test_should_send_notification_for_degraded_service(notification_service):
    """Test that notifications are sent for DEGRADED services."""
    service_info = ServiceInfo(
        service_name="test-service",
        status=ServiceStatus.DEGRADED,
        last_check_in=datetime.now(timezone.utc),
        check_in_count=1,
    )

    assert notification_service._should_send_notification(service_info)


def test_should_not_send_notification_for_up_service(notification_service):
    """Test that notifications are not sent for UP services without previous status."""
    service_info = ServiceInfo(
        service_name="test-service",
        status=ServiceStatus.UP,
        last_check_in=datetime.now(timezone.utc),
        check_in_count=1,
    )

    assert not notification_service._should_send_notification(service_info)


def test_generate_email_content_alert(notification_service, service_info):
    """Test email content generation for alerts."""
    subject, plain_text, html_content = notification_service._generate_email_content(service_info)

    assert "Service Alert" in subject
    assert service_info.service_name in subject
    assert service_info.service_name in plain_text
    assert service_info.status.value.upper() in plain_text
    assert service_info.service_name in html_content


def test_generate_email_content_recovery(notification_service):
    """Test email content generation for recovery notifications."""
    service_info = ServiceInfo(
        service_name="test-service",
        status=ServiceStatus.UP,
        last_check_in=datetime.now(timezone.utc),
        check_in_count=2,
    )

    subject, plain_text, html_content = notification_service._generate_email_content(service_info, is_recovery=True)

    assert "Service Recovered" in subject
    assert "Service Monitor Alert" in plain_text
    assert service_info.service_name in html_content


def test_notification_history_tracking(notification_service, service_info):
    """Test that notification history is properly tracked."""
    # Initially empty
    assert len(notification_service._notification_history) == 0

    # After tracking a notification
    notification_service._notification_history[service_info.service_name] = NotificationHistory(
        service_name=service_info.service_name,
        last_notification=datetime.now(timezone.utc),
        last_status=service_info.status,
        notification_count=1,
    )

    history = notification_service.get_notification_history()
    assert len(history) == 1
    assert service_info.service_name in history


def test_clear_notification_history(notification_service, service_info):
    """Test clearing notification history."""
    # Add some history
    notification_service._notification_history[service_info.service_name] = NotificationHistory(
        service_name=service_info.service_name,
        last_notification=datetime.now(timezone.utc),
        last_status=service_info.status,
        notification_count=1,
    )

    # Clear specific service
    notification_service.clear_notification_history(service_info.service_name)
    assert len(notification_service._notification_history) == 0

    # Add history again and clear all
    notification_service._notification_history[service_info.service_name] = NotificationHistory(
        service_name=service_info.service_name,
        last_notification=datetime.now(timezone.utc),
        last_status=service_info.status,
        notification_count=1,
    )

    notification_service.clear_notification_history()
    assert len(notification_service._notification_history) == 0


@pytest.mark.asyncio
async def test_send_email_success(notification_service):
    """Test successful email sending."""
    with patch.object(notification_service._client, "post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        result = await notification_service._send_email(
            "test@example.com", "Test Subject", "Test Message", "<html>Test</html>"
        )

        assert result is True
        mock_post.assert_called_once()
