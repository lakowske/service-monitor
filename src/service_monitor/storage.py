"""Storage layer for service monitoring data."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .models import ServiceInfo, ServiceStatus

logger = logging.getLogger(__name__)


class InMemoryStorage:
    """In-memory storage implementation for service data."""

    def __init__(self) -> None:
        """Initialize the in-memory storage."""
        self._services: Dict[str, ServiceInfo] = {}
        logger.info("InMemoryStorage initialized - storage_type: in_memory")

    def update_service(
        self,
        service_name: str,
        status: ServiceStatus,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> ServiceInfo:
        """Update or create a service entry.

        Args:
            service_name: Name of the service
            status: Current status of the service
            message: Optional status message
            metadata: Optional service metadata

        Returns:
            Updated ServiceInfo object
        """
        logger.debug(
            f"Updating service - service_name: {service_name}, status: {status.value}, "
            f"message: {message}, metadata_keys: {list(metadata.keys()) if metadata else []}"
        )

        current_time = datetime.now()

        if service_name in self._services:
            service = self._services[service_name]
            service.status = status
            service.last_check_in = current_time
            service.message = message
            service.check_in_count += 1
            if metadata:
                service.metadata.update(metadata)
            logger.info(
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

        return service

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

    def get_all_services(self) -> List[ServiceInfo]:
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
        else:
            logger.warning(f"Service removal failed - service_name: {service_name} not found")
            return False

    def get_services_by_status(self, status: ServiceStatus) -> List[ServiceInfo]:
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