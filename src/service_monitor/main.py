"""Main FastAPI application for the service monitor."""

import logging
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .models import HealthResponse, ServiceCheckIn, ServiceInfo
from .storage import InMemoryStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Service Monitor",
    description="A service for monitoring the health and status of other services",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize storage
storage = InMemoryStorage()


def reset_storage() -> None:
    """Reset the storage for testing purposes."""
    global storage
    storage = InMemoryStorage()

# Track application start time for uptime calculation
app_start_time = time.time()

logger.info("Service Monitor application starting - version: 0.1.0")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for the service monitor itself.

    Returns:
        HealthResponse: Current health status and metrics
    """
    current_time = datetime.now()
    uptime = time.time() - app_start_time
    monitored_services = storage.get_service_count()

    logger.debug(
        f"Health check requested - uptime: {uptime:.2f}s, monitored_services: {monitored_services}, "
        f"timestamp: {current_time}"
    )

    return HealthResponse(
        status="healthy",
        timestamp=current_time,
        uptime_seconds=uptime,
        monitored_services=monitored_services,
    )


@app.post("/services/checkin", response_model=ServiceInfo, status_code=status.HTTP_201_CREATED)
async def service_checkin(checkin: ServiceCheckIn) -> ServiceInfo:
    """Handle service check-in requests.

    Args:
        checkin: ServiceCheckIn data containing service status information

    Returns:
        ServiceInfo: Updated service information

    Raises:
        HTTPException: If service name is invalid
    """
    if not checkin.service_name.strip():
        logger.error(f"Invalid service check-in attempt - empty service_name, status: {checkin.status.value}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service name cannot be empty",
        )

    logger.info(
        f"Service check-in received - service_name: {checkin.service_name}, status: {checkin.status.value}, "
        f"message: {checkin.message}"
    )

    try:
        service_info = storage.update_service(
            service_name=checkin.service_name,
            status=checkin.status,
            message=checkin.message,
            metadata=checkin.metadata,
        )
        logger.info(
            f"Service check-in processed successfully - service_name: {checkin.service_name}, "
            f"check_in_count: {service_info.check_in_count}"
        )
        return service_info
    except Exception as e:
        logger.error(
            f"Service check-in failed - service_name: {checkin.service_name}, error: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process service check-in",
        ) from e


@app.get("/services", response_model=List[ServiceInfo])
async def get_all_services() -> List[ServiceInfo]:
    """Get information about all monitored services.

    Returns:
        List[ServiceInfo]: List of all registered services
    """
    logger.debug("All services requested")
    services = storage.get_all_services()
    logger.info(f"All services retrieved - count: {len(services)}")
    return services


@app.get("/services/{service_name}", response_model=ServiceInfo)
async def get_service(service_name: str) -> ServiceInfo:
    """Get information about a specific service.

    Args:
        service_name: Name of the service to retrieve

    Returns:
        ServiceInfo: Service information

    Raises:
        HTTPException: If service is not found
    """
    logger.debug(f"Service information requested - service_name: {service_name}")
    service = storage.get_service(service_name)
    if service is None:
        logger.warning(f"Service not found - service_name: {service_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found",
        )
    logger.info(f"Service information retrieved - service_name: {service_name}, status: {service.status.value}")
    return service


@app.delete("/services/{service_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_service(service_name: str) -> None:
    """Remove a service from monitoring.

    Args:
        service_name: Name of the service to remove

    Raises:
        HTTPException: If service is not found
    """
    logger.info(f"Service removal requested - service_name: {service_name}")
    if not storage.remove_service(service_name):
        logger.warning(f"Service removal failed - service_name: {service_name} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found",
        )
    logger.info(f"Service removed successfully - service_name: {service_name}")


@app.get("/services/status/{status_filter}", response_model=List[ServiceInfo])
async def get_services_by_status(status_filter: str) -> List[ServiceInfo]:
    """Get all services with a specific status.

    Args:
        status_filter: Status to filter by (up, down, degraded, unknown)

    Returns:
        List[ServiceInfo]: List of services with the specified status

    Raises:
        HTTPException: If status filter is invalid
    """
    logger.debug(f"Services by status requested - status_filter: {status_filter}")
    try:
        from .models import ServiceStatus

        status_enum = ServiceStatus(status_filter)
        services = storage.get_services_by_status(status_enum)
        logger.info(f"Services by status retrieved - status: {status_filter}, count: {len(services)}")
        return services
    except ValueError as e:
        logger.error(f"Invalid status filter - status_filter: {status_filter}, error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter: {status_filter}. Valid values: up, down, degraded, unknown",
        ) from e


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors.

    Args:
        request: FastAPI request object
        exc: Exception that was raised

    Returns:
        JSONResponse: Error response
    """
    logger.error(
        f"Unhandled exception - path: {request.url.path}, method: {request.method}, error: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Service Monitor server - host: 0.0.0.0, port: 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)