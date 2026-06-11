from __future__ import annotations
import time
from app.queue.worker import VIPEXWorker
from app.storage.bootstrap import bootstrap

bootstrap()
worker = VIPEXWorker()
print("VIPEX ACA worker started")
while True:
    result = worker.process_one()
    print(result)
    if result.get("status") == "empty":
        time.sleep(5)
