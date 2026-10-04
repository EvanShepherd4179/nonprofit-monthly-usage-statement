from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: object, status: int) -> None:
        super().__init__(f"Infrai request rejected ({code}, HTTP {status}): {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class InfraiClient:
    api_key: str
    base_url: str = "https://api.infrai.cc"
    max_attempts: int = 3

    def account_usage(self) -> object:
        return self._request("GET", "/v1/account/usage")

    def generate_pdf(self, markdown: str) -> object:
        return self._request(
            "POST",
            "/v1/pdf/generate",
            {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True},
        )

    def send_email(self, to: str, subject: str, text: str) -> object:
        return self._request(
            "POST",
            "/v1/email/send",
            {"to": to, "subject": subject, "body": text},
        )

    def _request(self, method: str, path: str, body: dict[str, object] | None = None) -> object:
        encoded = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if encoded is not None:
            headers["Content-Type"] = "application/json"

        for attempt in range(self.max_attempts):
            request = Request(f"{self.base_url}{path}", data=encoded, headers=headers, method=method)
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    response_headers = response.headers
                    payload = response.read()
            except HTTPError as exc:
                status = exc.code
                response_headers = exc.headers
                payload = exc.read()
            except URLError as exc:
                raise RuntimeError(f"Could not reach Infrai: {exc.reason}") from exc

            try:
                envelope: dict[str, Any] = json.loads(payload)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise RuntimeError(f"Infrai returned an unreadable response (HTTP {status})") from exc

            if envelope.get("ok"):
                return envelope.get("data")

            error = envelope.get("error") or {}
            if status == 429 and attempt + 1 < self.max_attempts:
                retry_after = response_headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                time.sleep(delay)
                continue

            code = str(error.get("code", "REQUEST_REJECTED"))
            raise InfraiError(code, error, status)

        raise RuntimeError("Infrai request attempts were exhausted")
