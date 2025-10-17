"""Email notification service for service monitoring alerts."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import BaseModel

from .config import config
from .models import ServiceInfo, ServiceStatus

logger = logging.getLogger(__name__)


class NotificationHistory(BaseModel):
    """Track notification history to prevent spam."""

    service_name: str
    last_notification: datetime
    last_status: ServiceStatus
    notification_count: int = 0


class EmailNotificationService:
    """Service for sending email notifications about service status changes."""

    def __init__(self) -> None:
        """Initialize the email notification service."""
        self._notification_history: dict[str, NotificationHistory] = {}
        self._client = httpx.AsyncClient(timeout=30.0)
        logger.info(
            f"EmailNotificationService initialized - enabled: {config.notifications.enabled}, "
            f"recipients: {config.notifications.recipients}"
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _should_send_notification(self, service: ServiceInfo, previous_status: Optional[ServiceStatus] = None) -> bool:
        """Determine if a notification should be sent for this service status change."""
        if not config.notifications.enabled:
            logger.debug(f"Notifications disabled - skipping for {service.service_name}")
            return False

        # Get notification history for this service
        history = self._notification_history.get(service.service_name)
        current_time = datetime.now(timezone.utc)

        # If no previous status provided, check history
        if previous_status is None and history:
            previous_status = history.last_status

        # Don't send notification if status hasn't changed
        if previous_status == service.status:
            logger.debug(f"No status change for {service.service_name} - skipping notification")
            return False

        # Check if this is a recovery notification (UP from DOWN/DEGRADED)
        is_recovery = (
            previous_status in [ServiceStatus.DOWN, ServiceStatus.DEGRADED] and service.status == ServiceStatus.UP
        )

        # Check if this is an alert notification (DOWN or DEGRADED)
        is_alert = service.status in [ServiceStatus.DOWN, ServiceStatus.DEGRADED]

        # Determine if we should send this notification type
        should_send = False
        if is_alert:
            logger.info(f"Alert notification triggered for {service.service_name} - status: {service.status.value}")
            should_send = True
        elif is_recovery and config.notifications.send_recovery_notifications:
            logger.info(f"Recovery notification triggered for {service.service_name}")
            should_send = True
        else:
            logger.debug(f"No notification needed for {service.service_name} - status: {service.status.value}")
            return False

        # Apply cooldown check ONLY for alert notifications, NOT for recovery notifications
        # Recovery notifications bypass cooldown so users know immediately when services recover
        if should_send and is_alert and history:
            time_since_last = (current_time - history.last_notification).total_seconds() / 60
            if time_since_last < config.notifications.cooldown_minutes:
                logger.debug(
                    f"Cooldown active for {service.service_name} - "
                    f"{time_since_last:.1f}min < {config.notifications.cooldown_minutes}min"
                )
                return False

        return should_send

    def _generate_email_content(self, service: ServiceInfo, is_recovery: bool = False) -> tuple[str, str, str]:
        """Generate email subject, plain text, and HTML content."""
        status_emoji = {
            ServiceStatus.UP: "✅",
            ServiceStatus.DOWN: "❌",
            ServiceStatus.DEGRADED: "⚠️",
            ServiceStatus.UNKNOWN: "❓",
        }

        if is_recovery:
            subject = f"🎉 Service Recovered: {service.service_name}"
            action = "recovered and is now"
            color = "#48bb78"  # Green
        else:
            subject = f"🚨 Service Alert: {service.service_name} is {service.status.value.upper()}"
            action = "is now"
            color = "#f56565" if service.status == ServiceStatus.DOWN else "#ed8936"  # Red or Orange

        # Plain text content
        plain_text = f"""Service Monitor Alert

Service: {service.service_name}
Status: {status_emoji[service.status]} {service.status.value.upper()}
Time: {service.last_check_in.strftime('%Y-%m-%d %H:%M:%S UTC')}
Check-ins: {service.check_in_count}
"""

        if service.message:
            plain_text += f"Message: {service.message}\n"

        if service.metadata:
            plain_text += "\nMetadata:\n"
            for key, value in service.metadata.items():
                plain_text += f"  {key}: {value}\n"

        if config.notifications.include_dashboard_link:
            dashboard_url = f"{config.notifications.dashboard_base_url}/service/{service.service_name}"
            plain_text += f"\nView Details: {dashboard_url}"

        # HTML content
        metadata_html = ""
        if service.metadata:
            metadata_rows = "".join(
                [
                    f"<tr><td style='padding: 4px 8px; border-bottom: 1px solid #eee;'><strong>{key}:</strong></td>"
                    f"<td style='padding: 4px 8px; border-bottom: 1px solid #eee;'>{value}</td></tr>"
                    for key, value in service.metadata.items()
                ]
            )
            metadata_html = f"""
            <h3 style='color: #333; margin: 20px 0 10px 0;'>Metadata</h3>
            <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                {metadata_rows}
            </table>
            """

        dashboard_link_html = ""
        if config.notifications.include_dashboard_link:
            dashboard_url = f"{config.notifications.dashboard_base_url}/service/{service.service_name}"
            dashboard_link_html = f"""
            <div style='text-align: center; margin: 30px 0;'>
                <a href='{dashboard_url}'
                   style='background: #4299e1; color: white; padding: 12px 24px; text-decoration: none;
                          border-radius: 6px; display: inline-block; font-weight: 500;'>
                    View Service Details
                </a>
            </div>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
        </head>
        <body style='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6; margin: 0; padding: 0; background: #f8fafc;'>
            <div style='max-width: 600px; margin: 0 auto; background: white; border-radius: 8px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;'>

                <!-- Header -->
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 20px; text-align: center;'>
                    <h1 style='margin: 0; font-size: 24px;'>🔍 Service Monitor</h1>
                </div>

                <!-- Alert Banner -->
                <div style='background: {color}; color: white; padding: 15px; text-align: center; font-weight: 500;'>
                    <div style='font-size: 18px;'>{status_emoji[service.status]} {service.service_name} {action} {service.status.value.upper()}</div>
                </div>

                <!-- Content -->
                <div style='padding: 20px;'>
                    <h2 style='color: #2d3748; margin: 0 0 20px 0; font-size: 20px;'>Service Details</h2>

                    <table style='width: 100%; border-collapse: collapse; margin-bottom: 20px;'>
                        <tr>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0; width: 30%;'>
                                <strong>Service:</strong>
                            </td>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                {service.service_name}
                            </td>
                        </tr>
                        <tr>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                <strong>Status:</strong>
                            </td>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                <span style='background: {color}; color: white; padding: 4px 8px;
                                           border-radius: 12px; font-size: 12px; font-weight: 500;'>
                                    {status_emoji[service.status]} {service.status.value.upper()}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                <strong>Time:</strong>
                            </td>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                {service.last_check_in.strftime('%Y-%m-%d %H:%M:%S UTC')}
                            </td>
                        </tr>
                        <tr>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                <strong>Check-ins:</strong>
                            </td>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                {service.check_in_count}
                            </td>
                        </tr>
                        {f'''<tr>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;'>
                                <strong>Message:</strong>
                            </td>
                            <td style='padding: 8px 12px; border-bottom: 1px solid #e2e8f0;
                                     font-style: italic; color: #4a5568;'>
                                {service.message}
                            </td>
                        </tr>''' if service.message else ''}
                    </table>

                    {metadata_html}

                    {dashboard_link_html}
                </div>

                <!-- Footer -->
                <div style='background: #f7fafc; padding: 15px; text-align: center;
                           color: #718096; font-size: 14px; border-top: 1px solid #e2e8f0;'>
                    This is an automated alert from Service Monitor<br>
                    <a href='{config.notifications.dashboard_base_url}'
                       style='color: #4299e1; text-decoration: none;'>View Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """

        return subject, plain_text, html_content

    async def _send_email(self, to: str, subject: str, message: str, html_content: str) -> bool:
        """Send email via Gmail LLM API with retry logic."""
        payload = {"to": to, "subject": subject, "message": message, "html_content": html_content}

        for attempt in range(config.notifications.retry_attempts):
            try:
                logger.debug(f"Sending email attempt {attempt + 1}/{config.notifications.retry_attempts} to {to}")

                response = await self._client.post(
                    f"{config.notifications.gmail_api_url}/api/emails/send", json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        logger.info(f"Email sent successfully to {to} - subject: {subject}")
                        return True
                    logger.error(f"Gmail API returned success=false - response: {result}")
                else:
                    logger.error(f"Gmail API request failed - status: {response.status_code}, text: {response.text}")

            except Exception as e:
                logger.error(f"Error sending email to {to} (attempt {attempt + 1}): {str(e)}", exc_info=True)

            # Wait before retry (except for last attempt)
            if attempt < config.notifications.retry_attempts - 1:
                await asyncio.sleep(config.notifications.retry_delay_seconds)

        logger.error(f"Failed to send email to {to} after {config.notifications.retry_attempts} attempts")
        return False

    async def send_service_notification(
        self, service: ServiceInfo, previous_status: Optional[ServiceStatus] = None
    ) -> bool:
        """Send notification for service status change."""
        if not self._should_send_notification(service, previous_status):
            return False

        # Determine if this is a recovery notification
        is_recovery = (
            previous_status in [ServiceStatus.DOWN, ServiceStatus.DEGRADED] and service.status == ServiceStatus.UP
        )

        # Generate email content
        subject, plain_text, html_content = self._generate_email_content(service, is_recovery)

        # Send to all recipients
        success_count = 0
        for recipient in config.notifications.recipients:
            if await self._send_email(recipient, subject, plain_text, html_content):
                success_count += 1

        # Update notification history
        current_time = datetime.now(timezone.utc)
        if service.service_name in self._notification_history:
            history = self._notification_history[service.service_name]
            history.last_notification = current_time
            history.last_status = service.status
            history.notification_count += 1
        else:
            self._notification_history[service.service_name] = NotificationHistory(
                service_name=service.service_name,
                last_notification=current_time,
                last_status=service.status,
                notification_count=1,
            )

        logger.info(
            f"Notification sent for {service.service_name} - "
            f"success: {success_count}/{len(config.notifications.recipients)}, "
            f"type: {'recovery' if is_recovery else 'alert'}"
        )

        return success_count > 0

    def get_notification_history(self) -> dict[str, NotificationHistory]:
        """Get notification history for all services."""
        return self._notification_history.copy()

    def clear_notification_history(self, service_name: Optional[str] = None) -> None:
        """Clear notification history for a specific service or all services."""
        if service_name:
            self._notification_history.pop(service_name, None)
            logger.info(f"Cleared notification history for {service_name}")
        else:
            self._notification_history.clear()
            logger.info("Cleared all notification history")


# Global notification service instance
notification_service = EmailNotificationService()
