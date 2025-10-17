"""Main FastAPI application for the service monitor."""

import asyncio
import contextlib
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import HealthResponse, ServiceCheckIn, ServiceInfo, ServiceStatus
from .monitored_services import MonitoredService, MonitoredServiceManager
from .notifications import notification_service
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

# Initialize storage and monitored services manager
storage = InMemoryStorage()
monitored_services_manager = MonitoredServiceManager()

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def reset_storage() -> None:
    """Reset the storage for testing purposes."""
    global storage
    storage = InMemoryStorage()


# Track application start time for uptime calculation
app_start_time = time.time()

# Background task for checking stale services
stale_check_task: Optional[asyncio.Task] = None

logger.info("Service Monitor application starting - version: 0.1.0")


async def check_stale_services_loop() -> None:
    """Background task to periodically check for stale services."""
    logger.info("Starting stale service checker - check interval: 30s, timeout: 150s")

    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds

            # Check for stale services
            stale_services = storage.check_stale_services(timeout_seconds=150)

            # Send notifications for services that became stale
            for service_info, previous_status in stale_services:
                try:
                    await notification_service.send_service_notification(service_info, previous_status)
                    logger.info(
                        f"Notification sent for stale service - service_name: {service_info.service_name}, "
                        f"previous_status: {previous_status.value}, current_status: {service_info.status.value}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification for stale service {service_info.service_name}: {str(e)}",
                        exc_info=True,
                    )

        except asyncio.CancelledError:
            logger.info("Stale service checker cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in stale service checker: {str(e)}", exc_info=True)


@app.on_event("startup")
async def startup_event() -> None:
    """Handle application startup."""
    global stale_check_task

    logger.info("Starting monitored services health checking")
    await monitored_services_manager.start_monitoring(storage)

    # Start background task to check for stale services
    stale_check_task = asyncio.create_task(check_stale_services_loop())
    logger.info("Started background stale service checker")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Handle application shutdown."""
    logger.info("Service Monitor shutting down")

    # Cancel stale check task
    if stale_check_task:
        stale_check_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await stale_check_task

    await monitored_services_manager.close()
    await notification_service.close()


# Web Interface Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Main dashboard showing all services."""
    services = storage.get_all_services()

    # Count services by status
    status_counts = {status.value: 0 for status in ServiceStatus}
    for service in services:
        status_counts[service.status.value] += 1

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "services": services,
            "total_services": len(services),
            "status_counts": status_counts,
            "uptime_seconds": time.time() - app_start_time,
        },
    )


@app.get("/service/{service_name}", response_class=HTMLResponse)
async def service_detail(request: Request, service_name: str) -> HTMLResponse:
    """Detailed view of a specific service."""
    service = storage.get_service(service_name)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found",
        )

    return templates.TemplateResponse(
        "service_detail.html",
        {
            "request": request,
            "service": service,
        },
    )


# Widget Routes
@app.get("/widgets/summary", response_class=HTMLResponse)
async def widget_summary(request: Request, theme: str = "light") -> HTMLResponse:
    """Summary widget showing status counts."""
    services = storage.get_all_services()

    # Count services by status
    status_counts = {status.value: 0 for status in ServiceStatus}
    for service in services:
        status_counts[service.status.value] += 1

    # Build dashboard URL (use request base URL)
    dashboard_url = str(request.base_url).rstrip("/")

    return templates.TemplateResponse(
        "widgets/summary.html",
        {
            "request": request,
            "status_counts": status_counts,
            "dashboard_url": dashboard_url,
            "theme": theme,
        },
    )


@app.get("/widgets/critical", response_class=HTMLResponse)
async def widget_critical(request: Request, theme: str = "light") -> HTMLResponse:
    """Critical alerts widget showing only DOWN/DEGRADED services."""
    # Get services that are down or degraded
    down_services = storage.get_services_by_status(ServiceStatus.DOWN)
    degraded_services = storage.get_services_by_status(ServiceStatus.DEGRADED)
    critical_services = down_services + degraded_services

    # Sort by status (DOWN first, then DEGRADED)
    critical_services.sort(key=lambda s: (s.status.value != "down", s.service_name))

    # Build dashboard URL
    dashboard_url = str(request.base_url).rstrip("/")

    return templates.TemplateResponse(
        "widgets/critical.html",
        {
            "request": request,
            "critical_services": critical_services,
            "dashboard_url": dashboard_url,
            "theme": theme,
        },
    )


@app.get("/widgets/service/{service_name}", response_class=HTMLResponse)
async def widget_service(request: Request, service_name: str, theme: str = "light") -> HTMLResponse:
    """Single service widget showing detailed information."""
    service = storage.get_service(service_name)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found",
        )

    # Build service detail URL
    service_url = f"{str(request.base_url).rstrip('/')}/service/{service_name}"

    return templates.TemplateResponse(
        "widgets/service.html",
        {
            "request": request,
            "service": service,
            "service_url": service_url,
            "theme": theme,
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for the service monitor itself.

    Returns:
        HealthResponse: Current health status and metrics
    """
    current_time = datetime.now(timezone.utc)
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
        service_info, previous_status = storage.update_service(
            service_name=checkin.service_name,
            status=checkin.status,
            message=checkin.message,
            metadata=checkin.metadata,
        )

        # Send notification if status changed to a problem state or recovered
        if previous_status is not None:
            try:
                await notification_service.send_service_notification(service_info, previous_status)
            except Exception as notification_error:
                logger.error(
                    f"Failed to send notification for {checkin.service_name}: {str(notification_error)}", exc_info=True
                )
                # Don't fail the check-in if notification fails

        logger.info(
            f"Service check-in processed successfully - service_name: {checkin.service_name}, "
            f"check_in_count: {service_info.check_in_count}, "
            f"status_changed: {previous_status is not None}"
        )
        return service_info
    except Exception as e:
        logger.error(f"Service check-in failed - service_name: {checkin.service_name}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process service check-in",
        ) from e


@app.get("/services", response_model=list[ServiceInfo])
async def get_all_services() -> list[ServiceInfo]:
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


@app.get("/services/status/{status_filter}", response_model=list[ServiceInfo])
async def get_services_by_status(status_filter: str) -> list[ServiceInfo]:
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


# Notification Management Endpoints
@app.get("/notifications/history")
async def get_notification_history() -> dict:
    """Get notification history for all services."""
    history = notification_service.get_notification_history()
    return {
        "success": True,
        "history": {
            service_name: {
                "service_name": hist.service_name,
                "last_notification": hist.last_notification.isoformat(),
                "last_status": hist.last_status.value,
                "notification_count": hist.notification_count,
            }
            for service_name, hist in history.items()
        },
        "total_services": len(history),
    }


@app.post("/notifications/test")
async def send_test_notification(service_name: str = "test-service") -> dict:
    """Send a test notification for debugging purposes."""
    # Create a test service with DOWN status
    test_service = ServiceInfo(
        service_name=service_name,
        status=ServiceStatus.DOWN,
        last_check_in=datetime.now(timezone.utc),
        message="This is a test notification from the Service Monitor",
        metadata={"source": "test_endpoint", "version": "test"},
        check_in_count=1,
    )

    try:
        success = await notification_service.send_service_notification(test_service, ServiceStatus.UP)
        return {
            "success": success,
            "message": f"Test notification {'sent' if success else 'failed'} for {service_name}",
        }
    except Exception as e:
        logger.error(f"Test notification failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Test notification failed: {str(e)}",
        }


@app.delete("/notifications/history/{service_name}")
async def clear_service_notification_history(service_name: str) -> dict:
    """Clear notification history for a specific service."""
    notification_service.clear_notification_history(service_name)
    return {
        "success": True,
        "message": f"Notification history cleared for {service_name}",
    }


@app.delete("/notifications/history")
async def clear_all_notification_history() -> dict:
    """Clear notification history for all services."""
    notification_service.clear_notification_history()
    return {
        "success": True,
        "message": "All notification history cleared",
    }


# Monitored Services Management Endpoints
@app.get("/monitored-services")
async def get_monitored_services() -> dict:
    """Get all monitored services configurations."""
    services = monitored_services_manager.get_all_services()
    return {
        "success": True,
        "services": [service.model_dump() for service in services],
        "total": len(services),
    }


@app.get("/monitored-services/{service_name}")
async def get_monitored_service(service_name: str) -> dict:
    """Get a specific monitored service configuration."""
    service = monitored_services_manager.get_service(service_name)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored service '{service_name}' not found",
        )
    return {
        "success": True,
        "service": service.model_dump(),
    }


@app.post("/monitored-services")
async def add_monitored_service(service: MonitoredService) -> dict:
    """Add or update a monitored service."""
    # Add the service to configuration
    monitored_services_manager.add_service(service)

    # Start monitoring for this service if enabled
    if service.enabled:
        await monitored_services_manager.start_monitoring(storage)

    logger.info(f"Monitored service added/updated: {service.name}")
    return {
        "success": True,
        "message": f"Monitored service '{service.name}' added/updated successfully",
        "service": service.model_dump(),
    }


@app.put("/monitored-services/{service_name}")
async def update_monitored_service(service_name: str, service: MonitoredService) -> dict:
    """Update a monitored service configuration."""
    if service.name != service_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service name in path must match service name in body",
        )

    existing = monitored_services_manager.get_service(service_name)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored service '{service_name}' not found",
        )

    # Stop monitoring for old configuration
    await monitored_services_manager.stop_monitoring(service_name)

    # Update the service
    monitored_services_manager.add_service(service)

    # Restart monitoring if enabled
    if service.enabled:
        await monitored_services_manager.start_monitoring(storage)

    logger.info(f"Monitored service updated: {service_name}")
    return {
        "success": True,
        "message": f"Monitored service '{service_name}' updated successfully",
        "service": service.model_dump(),
    }


@app.delete("/monitored-services/{service_name}")
async def delete_monitored_service(service_name: str) -> dict:
    """Remove a monitored service."""
    # Stop monitoring
    await monitored_services_manager.stop_monitoring(service_name)

    # Remove from configuration
    if not monitored_services_manager.remove_service(service_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored service '{service_name}' not found",
        )

    logger.info(f"Monitored service removed: {service_name}")
    return {
        "success": True,
        "message": f"Monitored service '{service_name}' removed successfully",
    }


@app.post("/monitored-services/{service_name}/check")
async def check_monitored_service(service_name: str) -> dict:
    """Manually trigger a health check for a monitored service."""
    service = monitored_services_manager.get_service(service_name)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monitored service '{service_name}' not found",
        )

    # Perform health check
    status_result, message, metadata = await monitored_services_manager.check_service_health(service)

    # Update storage
    storage.update_service(
        service_name=service.name,
        status=status_result,
        message=message,
        metadata=metadata,
    )

    return {
        "success": True,
        "service_name": service_name,
        "status": status_result.value,
        "message": message,
        "metadata": metadata,
    }


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
