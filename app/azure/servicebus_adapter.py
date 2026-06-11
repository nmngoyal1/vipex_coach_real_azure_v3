from __future__ import annotations
import json
from typing import Any
from app.settings import get_settings

class AzureServiceBusQueue:
    """Real Azure Service Bus queue adapter.

    This module is import-safe in LOCAL mode: Azure packages are imported only when the class is instantiated.
    Auth options:
    1. SERVICE_BUS_CONNECTION_STRING, or
    2. SERVICE_BUS_FULLY_QUALIFIED_NAMESPACE + DefaultAzureCredential / Managed Identity.
    """
    def __init__(self) -> None:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.servicebus import ServiceBusClient
        except ModuleNotFoundError as exc:
            raise RuntimeError("Azure Service Bus dependencies are not installed. Run `pip install -r requirements.txt` or use RUNTIME_MODE=LOCAL.") from exc
        self._ServiceBusClient = ServiceBusClient
        self._DefaultAzureCredential = DefaultAzureCredential
        self.settings = get_settings()
        if self.settings.service_bus_connection_string:
            self.client = ServiceBusClient.from_connection_string(self.settings.service_bus_connection_string)
        elif self.settings.service_bus_fully_qualified_namespace:
            self.client = ServiceBusClient(
                fully_qualified_namespace=self.settings.service_bus_fully_qualified_namespace,
                credential=DefaultAzureCredential(),
            )
        else:
            raise RuntimeError("Azure Service Bus is enabled but no namespace/connection string is configured")
        self.queue_name = self.settings.service_bus_queue_name

    def send(self, job_id: str, payload: dict[str, Any]) -> str:
        from azure.servicebus import ServiceBusMessage
        body = json.dumps(payload, ensure_ascii=False)
        with self.client.get_queue_sender(queue_name=self.queue_name) as sender:
            msg = ServiceBusMessage(body, message_id=job_id, content_type="application/json", correlation_id=payload.get("conversation_id"))
            sender.send_messages(msg)
        return job_id

    def receive_one(self) -> dict[str, Any] | None:
        receiver = self.client.get_queue_receiver(queue_name=self.queue_name, max_wait_time=5)
        receiver.__enter__()
        try:
            messages = receiver.receive_messages(max_message_count=1, max_wait_time=5)
            if not messages:
                receiver.__exit__(None, None, None)
                return None
            msg = messages[0]
            body = b"".join([bytes(b) for b in msg.body]).decode("utf-8")
            return {"message_id": msg.message_id, "payload": json.loads(body), "_raw_message": msg, "_receiver": receiver}
        except Exception:
            receiver.__exit__(None, None, None)
            raise

    def _close(self, received: dict[str, Any]) -> None:
        receiver = received.get("_receiver")
        if receiver:
            receiver.__exit__(None, None, None)

    def complete_received(self, received: dict[str, Any]) -> None:
        try:
            received["_receiver"].complete_message(received["_raw_message"])
        finally:
            self._close(received)

    def abandon_received(self, received: dict[str, Any], reason: str | None = None) -> None:
        try:
            received["_receiver"].abandon_message(received["_raw_message"])
        finally:
            self._close(received)

    def dead_letter_received(self, received: dict[str, Any], reason: str) -> None:
        try:
            received["_receiver"].dead_letter_message(received["_raw_message"], reason=reason[:4096])
        finally:
            self._close(received)
