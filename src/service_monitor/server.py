"""Server startup script for the service monitor."""

import logging
import sys
from typing import Optional

import uvicorn

logger = logging.getLogger(__name__)


def start_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info", reload: bool = False) -> None:
    """Start the service monitor server.

    Args:
        host: Host to bind the server to
        port: Port to bind the server to
        log_level: Logging level (debug, info, warning, error, critical)
        reload: Enable auto-reload for development
    """
    logger.info(
        f"Starting Service Monitor server - host: {host}, port: {port}, "
        f"log_level: {log_level}, reload: {reload}"
    )

    try:
        uvicorn.run(
            "service_monitor.main:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=reload,
        )
    except Exception as e:
        logger.error(f"Failed to start server - error: {str(e)}", exc_info=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for the service monitor server."""
    import argparse

    parser = argparse.ArgumentParser(description="Service Monitor Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level (default: info)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    )

    start_server(
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()