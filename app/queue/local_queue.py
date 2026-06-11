from __future__ import annotations
from app.storage.db import enqueue_message, dequeue_message, complete_message, abandon_or_deadletter, queue_stats

class LocalServiceBusQueue:
    """SQLite-backed Service Bus simulator.

    Keeps the local demo deterministic while preserving the same operational shape:
    active messages, locked messages, completed messages, and dead-letter messages.
    """
    def send(self, job_id: str, payload: dict) -> str:
        return enqueue_message(job_id, payload)

    def receive_one(self) -> dict | None:
        return dequeue_message()

    def complete(self, message_id: str) -> None:
        complete_message(message_id)

    def fail(self, message_id: str, error: str) -> None:
        abandon_or_deadletter(message_id, error)

    def stats(self) -> dict[str, int]:
        return queue_stats()
