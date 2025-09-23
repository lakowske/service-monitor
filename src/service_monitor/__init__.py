"""Service Monitor - A Python application for monitoring services and their health status.

This package provides a FastAPI-based service monitoring solution that allows other services
to check in and report their status. It includes features for tracking service health,
generating reports, and maintaining historical data.

Key Features:
- Service health check-ins
- Real-time status monitoring
- REST API with automatic documentation
- Comprehensive logging and error handling
- Extensible storage backends

Example:
    Basic usage of the service monitor:

    ```python
    import uvicorn
    from service_monitor.main import app

    uvicorn.run(app, host="0.0.0.0", port=8000)
    ```
"""

__version__ = "0.1.0"
__author__ = "Seth Lakowske"
__email__ = "lakowske@gmail.com"

# Make key classes available at package level
from .main import app
from .models import ServiceCheckIn, ServiceInfo, ServiceStatus
from .storage import InMemoryStorage

__all__ = ["app", "ServiceCheckIn", "ServiceInfo", "ServiceStatus", "InMemoryStorage"]
