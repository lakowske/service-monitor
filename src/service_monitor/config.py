"""Configuration management for the service monitor."""

import logging
import os

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationConfig(BaseModel):
    """Configuration for email notifications."""

    enabled: bool = Field(default=True, description="Whether email notifications are enabled")
    gmail_api_url: str = Field(default="http://127.0.0.1:7000", description="Gmail LLM API base URL")
    recipients: list[str] = Field(
        default_factory=lambda: ["lakowske@gmail.com"], description="List of email recipients for notifications"
    )
    cooldown_minutes: int = Field(default=60, description="Minimum time between notifications for the same service")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed email sends")
    retry_delay_seconds: int = Field(default=5, description="Delay between retry attempts in seconds")
    send_recovery_notifications: bool = Field(
        default=True, description="Whether to send notifications when services recover"
    )
    include_dashboard_link: bool = Field(default=True, description="Whether to include dashboard links in emails")
    dashboard_base_url: str = Field(
        default="http://localhost:8000", description="Base URL for the service monitor dashboard"
    )


class ServiceMonitorConfig(BaseModel):
    """Main configuration for the service monitor."""

    notifications: NotificationConfig = Field(
        default_factory=NotificationConfig, description="Email notification configuration"
    )
    log_level: str = Field(default="INFO", description="Logging level")

    @classmethod
    def from_env(cls) -> "ServiceMonitorConfig":
        """Create configuration from environment variables."""
        notifications = NotificationConfig(
            enabled=os.getenv("NOTIFICATIONS_ENABLED", "true").lower() == "true",
            gmail_api_url=os.getenv("GMAIL_API_URL", "http://127.0.0.1:7000"),
            recipients=os.getenv("NOTIFICATION_RECIPIENTS", "lakowske@gmail.com").split(","),
            cooldown_minutes=int(os.getenv("NOTIFICATION_COOLDOWN_MINUTES", "60")),
            retry_attempts=int(os.getenv("NOTIFICATION_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=int(os.getenv("NOTIFICATION_RETRY_DELAY", "5")),
            send_recovery_notifications=os.getenv("SEND_RECOVERY_NOTIFICATIONS", "true").lower() == "true",
            include_dashboard_link=os.getenv("INCLUDE_DASHBOARD_LINK", "true").lower() == "true",
            dashboard_base_url=os.getenv("DASHBOARD_BASE_URL", "http://localhost:8000"),
        )

        config = cls(notifications=notifications, log_level=os.getenv("LOG_LEVEL", "INFO"))

        logger.info(
            f"Configuration loaded - notifications_enabled: {config.notifications.enabled}, "
            f"recipients: {len(config.notifications.recipients)}"
        )

        return config


# Global configuration instance
config = ServiceMonitorConfig.from_env()
