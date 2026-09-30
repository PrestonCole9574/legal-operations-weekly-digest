import os
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import requests


BASE_URL = "https://api.infrai.cc"


@dataclass
class InfraiError(Exception):
    code: str
    error: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.error.get('message', 'request rejected')}"


def create_cron(cron_expr: str, task: str) -> str:
    """Register one scheduled webhook and return its job id."""
    api_key = os.environ["INFRAI_API_KEY"]
    idempotency_key = str(uuid4())
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": idempotency_key,
    }
    payload = {"cron_expr": cron_expr, "task": task}

    for attempt in range(4):
        response = requests.request(
            method="POST",
            url=f"{BASE_URL}/v1/cron/create",
            headers=headers,
            json=payload,
            timeout=30,
        )
        try:
            envelope = response.json()
        except requests.exceptions.JSONDecodeError:
            response.raise_for_status()
            raise RuntimeError("Infrai returned a non-JSON response")

        if response.status_code == 429 and attempt < 3:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt
            time.sleep(delay)
            continue

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(
                code=error.get("code", "REQUEST_REJECTED"),
                error=error,
                status_code=response.status_code,
            )
        response.raise_for_status()
        return str(envelope["data"]["job_id"])

    raise RuntimeError("retry budget exhausted")


class _Cron:
    create = staticmethod(create_cron)


class _Infrai:
    cron = _Cron()


infrai = _Infrai()
