from __future__ import annotations
import logging
from app.settings import get_settings

def configure_observability() -> None:
    """Enable Azure Monitor OpenTelemetry if configured; otherwise normal local logging."""
    settings = get_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if settings.applicationinsights_connection_string:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            configure_azure_monitor(connection_string=settings.applicationinsights_connection_string)
            logging.getLogger(__name__).info("Azure Monitor OpenTelemetry configured")
        except Exception as exc:
            logging.getLogger(__name__).warning("Azure Monitor setup skipped: %s", exc)
