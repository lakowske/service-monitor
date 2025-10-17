"""Monitored services configuration and health checking."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import httpx
from pydantic import BaseModel, Field

from .models import ServiceStatus

if TYPE_CHECKING:
    from .storage import InMemoryStorage

logger = logging.getLogger(__name__)


class MonitoredService(BaseModel):
    """Configuration for a monitored service."""

    name: str = Field(..., description="Unique name for the monitored service")
    health_url: str = Field(..., description="HTTP/HTTPS URL to check for service health")
    check_interval_seconds: int = Field(default=60, description="How often to check the service (in seconds)")
    timeout_seconds: int = Field(default=10, description="Request timeout in seconds")
    expected_status_code: int = Field(default=200, description="Expected HTTP status code for healthy service")
    enabled: bool = Field(default=True, description="Whether monitoring is enabled for this service")
    check_response_body: bool = Field(
        default=False, description="Whether to validate response body contains expected content"
    )
    expected_body_content: Optional[str] = Field(
        default=None, description="Expected content in response body (substring match)"
    )


class MonitoredServiceManager:
    """Manages monitored services configuration and health checking."""

    def __init__(self, config_file: str = "monitored_services.json") -> None:
        """Initialize the monitored service manager.

        Args:
            config_file: Path to the JSON configuration file
        """
        self.config_file = Path(config_file)
        self.services: dict[str, MonitoredService] = {}
        self.check_tasks: dict[str, asyncio.Task] = {}
        self._client: Optional[httpx.AsyncClient] = None
        self._load_config()
        logger.info(
            f"MonitoredServiceManager initialized - config_file: {self.config_file}, services: {len(self.services)}"
        )

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(follow_redirects=True)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and stop all check tasks."""
        # Cancel all running check tasks
        for task in self.check_tasks.values():
            task.cancel()

        # Wait for all tasks to complete
        if self.check_tasks:
            await asyncio.gather(*self.check_tasks.values(), return_exceptions=True)

        # Close HTTP client
        if self._client:
            await self._client.aclose()
            self._client = None

        logger.info("MonitoredServiceManager closed")

    def _load_config(self) -> None:
        """Load monitored services configuration from file."""
        if not self.config_file.exists():
            logger.info(f"No configuration file found at {self.config_file}, starting with empty config")
            return

        try:
            with self.config_file.open() as f:
                data = json.load(f)

            for service_data in data:
                service = MonitoredService(**service_data)
                self.services[service.name] = service

            logger.info(f"Loaded {len(self.services)} monitored services from {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to load monitored services config: {e}", exc_info=True)

    def _save_config(self) -> None:
        """Save monitored services configuration to file."""
        try:
            data = [service.model_dump() for service in self.services.values()]

            with self.config_file.open("w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(self.services)} monitored services to {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to save monitored services config: {e}", exc_info=True)

    def add_service(self, service: MonitoredService) -> None:
        """Add or update a monitored service.

        Args:
            service: The monitored service configuration
        """
        self.services[service.name] = service
        self._save_config()
        logger.info(f"Added/updated monitored service: {service.name}")

    def remove_service(self, name: str) -> bool:
        """Remove a monitored service.

        Args:
            name: Name of the service to remove

        Returns:
            True if service was removed, False if not found
        """
        if name in self.services:
            # Cancel the check task if running
            if name in self.check_tasks:
                self.check_tasks[name].cancel()
                del self.check_tasks[name]

            del self.services[name]
            self._save_config()
            logger.info(f"Removed monitored service: {name}")
            return True

        return False

    def get_service(self, name: str) -> Optional[MonitoredService]:
        """Get a monitored service by name.

        Args:
            name: Name of the service

        Returns:
            The monitored service or None if not found
        """
        return self.services.get(name)

    def get_all_services(self) -> list[MonitoredService]:
        """Get all monitored services.

        Returns:
            List of all monitored services
        """
        return list(self.services.values())

    async def check_service_health(self, service: MonitoredService) -> tuple[ServiceStatus, str, dict]:
        """Check the health of a monitored service.

        Args:
            service: The monitored service to check

        Returns:
            Tuple of (status, message, metadata)
        """
        metadata = {
            "health_url": service.health_url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            client = await self.get_client()
            logger.debug(f"Checking health of {service.name} at {service.health_url}")

            response = await client.get(service.health_url, timeout=service.timeout_seconds)

            metadata.update(
                {
                    "http_status_code": str(response.status_code),
                    "response_time_ms": f"{response.elapsed.total_seconds() * 1000:.2f}",
                }
            )

            # Check status code
            if response.status_code != service.expected_status_code:
                logger.warning(
                    f"Service {service.name} returned unexpected status code: {response.status_code} (expected {service.expected_status_code})"
                )
                return (
                    ServiceStatus.DEGRADED,
                    f"HTTP {response.status_code} (expected {service.expected_status_code})",
                    metadata,
                )

            # Check response body if configured
            if service.check_response_body and service.expected_body_content:
                body = response.text
                if service.expected_body_content not in body:
                    logger.warning(f"Service {service.name} response does not contain expected content")
                    return (
                        ServiceStatus.DEGRADED,
                        "Response body missing expected content",
                        metadata,
                    )

            logger.debug(f"Service {service.name} health check passed")
            return (
                ServiceStatus.UP,
                f"Health check passed ({response.status_code})",
                metadata,
            )

        except httpx.TimeoutException:
            logger.error(f"Health check timeout for {service.name} after {service.timeout_seconds}s")
            return (
                ServiceStatus.DOWN,
                f"Health check timed out after {service.timeout_seconds}s",
                {"error": "timeout"},
            )

        except httpx.ConnectError as e:
            logger.error(f"Connection error checking {service.name}: {e}")
            return (
                ServiceStatus.DOWN,
                "Cannot connect to service",
                {"error": "connection_error"},
            )

        except Exception as e:
            logger.error(f"Unexpected error checking {service.name}: {e}", exc_info=True)
            return (
                ServiceStatus.DOWN,
                f"Unexpected error: {str(e)}",
                {"error": "unexpected_error"},
            )

    async def start_monitoring(self, storage: "InMemoryStorage") -> None:
        """Start monitoring all enabled services.

        Args:
            storage: The storage instance to update service status
        """
        logger.info("Starting monitoring for all enabled services")

        for service in self.services.values():
            if service.enabled and service.name not in self.check_tasks:
                task = asyncio.create_task(self._monitor_service_loop(service, storage))
                self.check_tasks[service.name] = task
                logger.info(f"Started monitoring task for {service.name}")

    async def stop_monitoring(self, service_name: Optional[str] = None) -> None:
        """Stop monitoring for a specific service or all services.

        Args:
            service_name: Name of service to stop monitoring, or None to stop all
        """
        if service_name:
            if service_name in self.check_tasks:
                self.check_tasks[service_name].cancel()
                del self.check_tasks[service_name]
                logger.info(f"Stopped monitoring task for {service_name}")
        else:
            for _name, task in list(self.check_tasks.items()):
                task.cancel()
            self.check_tasks.clear()
            logger.info("Stopped all monitoring tasks")

    async def _monitor_service_loop(self, service: MonitoredService, storage: "InMemoryStorage") -> None:
        """Background loop to periodically check a service.

        Args:
            service: The monitored service configuration
            storage: The storage instance to update service status
        """
        logger.info(f"Starting monitor loop for {service.name} - interval: {service.check_interval_seconds}s")

        while True:
            try:
                # Check service health
                status, message, metadata = await self.check_service_health(service)

                # Update service status in storage
                storage.update_service(
                    service_name=service.name,
                    status=status,
                    message=message,
                    metadata=metadata,
                )

                logger.debug(f"Updated status for {service.name}: {status.value} - {message}")

            except asyncio.CancelledError:
                logger.info(f"Monitor loop cancelled for {service.name}")
                raise

            except Exception as e:
                logger.error(f"Error in monitor loop for {service.name}: {e}", exc_info=True)

            # Wait for next check interval
            await asyncio.sleep(service.check_interval_seconds)
