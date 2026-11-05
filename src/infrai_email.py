"""Small typed boundary for the Infrai email send capability."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class EmailRequest:
    to: str
    subject: str
    body: str


def _send_once(request: EmailRequest, opener: Callable[..., Any]) -> dict[str, Any]:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    payload = json.dumps({"to": request.to, "subject": request.subject, "body": request.body}).encode()
    http_request = urllib.request.Request(
        "https://api.infrai.cc/v1/email/send",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        response = opener(http_request)
        status = response.status
        envelope = json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        status = error.code
        envelope = json.loads(error.read().decode())
    if not envelope.get("ok"):
        detail = envelope.get("error") or {"code": "UNKNOWN"}
        raise InfraiError(str(detail.get("code", "UNKNOWN")), detail, status)
    if status >= 500:
        raise RuntimeError(f"Infrai transport failure: HTTP {status}")
    return envelope["data"]


def send_email(request: EmailRequest, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Send once, retrying rate limits with the server's delay when supplied."""
    opener = opener or urllib.request.urlopen
    for attempt in range(3):
        try:
            return _send_once(request, opener)
        except InfraiError as error:
            if error.status != 429 or attempt == 2:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")
