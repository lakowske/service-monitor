"""Storage layer for service monitoring data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import ServiceInfo, ServiceStatus

logger = logging.getLogger(__name__)

# Default timeout for check-in services (150 seconds = 2.5 minutes)
DEFAULT_CHECKIN_TIMEOUT_SECONDS = 150


class InMemoryStorage:
    """In-memory storage implementation for service data."""

    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._services: dict[str, ServiceInfo] = {}
        logger.info("InMemoryStorage initialized - storage_type: in_memory")

    def update_service(
        self,
        service_name: str,
        status: ServiceStatus,
        message: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> tuple[ServiceInfo, Optional[ServiceStatus]]:
        """Update or create a service entry.

        Args:
            service_name: Name of the service
            status: Current status of the service
            message: Optional status message
            metadata: Optional service metadata

        Returns:
            Tuple of (updated ServiceInfo object, previous status if changed)
        """
        logger.debug(
            f"Updating service - service_name: {service_name}, status: {status.value}, "
            f"message: {message}, metadata_keys: {list(metadata.keys()) if metadata else []}"
        )

        current_time = datetime.now(timezone.utc)
        previous_status: Optional[ServiceStatus] = None

        if service_name in self._services:
            service = self._services[service_name]
            previous_status = service.status

            # Check if status changed
            status_changed = previous_status != status

            service.status = status
            service.last_check_in = current_time
            service.message = message
            service.check_in_count += 1
            if metadata:
                if service.metadata is None:
                    service.metadata = {}
                service.metadata.update(metadata)

            if status_changed:
                logger.info(
                    f"Service status changed - service_name: {service_name}, "
                    f"previous: {previous_status.value}, current: {status.value}, "
                    f"check_in_count: {service.check_in_count}"
                )
            else:
                logger.debug(
                    f"Service updated - service_name: {service_name}, status: {status.value}, "
                    f"check_in_count: {service.check_in_count}"
                )
        else:
            service = ServiceInfo(
                service_name=service_name,
                status=status,
                last_check_in=current_time,
                message=message,
                metadata=metadata or {},
                check_in_count=1,
            )
            self._services[service_name] = service
            logger.info(
                f"New service registered - service_name: {service_name}, status: {status.value}, "
                f"timestamp: {current_time}"
            )

        # Return previous status only if it actually changed
        return service, previous_status if previous_status != status else None

    def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get information about a specific service.

        Args:
            service_name: Name of the service to retrieve

        Returns:
            ServiceInfo object if found, None otherwise
        """
        service = self._services.get(service_name)
        if service:
            logger.debug(f"Service retrieved - service_name: {service_name}, status: {service.status.value}")
        else:
            logger.warning(f"Service not found - service_name: {service_name}")
        return service

    def get_all_services(self) -> list[ServiceInfo]:
        """Get information about all registered services.

        Returns:
            List of all ServiceInfo objects
        """
        services = list(self._services.values())
        logger.debug(f"All services retrieved - count: {len(services)}")
        return services

    def remove_service(self, service_name: str) -> bool:
        """Remove a service from monitoring.

        Args:
            service_name: Name of the service to remove

        Returns:
            True if service was removed, False if not found
        """
        if service_name in self._services:
            del self._services[service_name]
            logger.info(f"Service removed - service_name: {service_name}")
            return True
        logger.warning(f"Service removal failed - service_name: {service_name} not found")
        return False

    def get_services_by_status(self, status: ServiceStatus) -> list[ServiceInfo]:
        """Get all services with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of ServiceInfo objects with the specified status
        """
        services = [service for service in self._services.values() if service.status == status]
        logger.debug(f"Services filtered by status - status: {status.value}, count: {len(services)}")
        return services

    def get_service_count(self) -> int:
        """Get the total number of monitored services.

        Returns:
            Number of services being monitored
        """
        count = len(self._services)
        logger.debug(f"Service count retrieved - count: {count}")
        return count

    def check_stale_services(
        self, timeout_seconds: int = DEFAULT_CHECKIN_TIMEOUT_SECONDS
    ) -> list[tuple[ServiceInfo, ServiceStatus]]:
        """Check for services that haven't checked in within the timeout period.

        Args:
            timeout_seconds: Number of seconds after which a service is considered stale

        Returns:
            List of tuples (ServiceInfo, previous_status) for services that became stale
        """
        current_time = datetime.now(timezone.utc)
        timeout_threshold = current_time - timedelta(seconds=timeout_seconds)
        stale_services = []

        for service_name, service in self._services.items():
            # Only check services that are currently marked as UP or DEGRADED and haven't checked in
            if (
                service.status in (ServiceStatus.UP, ServiceStatus.DEGRADED)
                and service.last_check_in < timeout_threshold
            ):
                time_since_checkin = (current_time - service.last_check_in).total_seconds()
                previous_status = service.status

                # Mark service as DOWN due to timeout
                service.status = ServiceStatus.DOWN
                service.message = f"No check-in for {int(time_since_checkin)}s (timeout: {timeout_seconds}s)"

                logger.warning(
                    f"Service marked as stale - service_name: {service_name}, "
                    f"last_check_in: {service.last_check_in}, "
                    f"time_since_checkin: {int(time_since_checkin)}s, "
                    f"previous_status: {previous_status.value}"
                )

                stale_services.append((service, previous_status))

        if stale_services:
            logger.info(f"Found {len(stale_services)} stale services")

        return stale_services
