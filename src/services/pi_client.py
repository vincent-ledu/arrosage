from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


class PiServiceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PiServiceConfig:
    base_url: str
    token: str | None
    timeout_connect: float
    timeout_read: float


def load_pi_service_config() -> PiServiceConfig | None:
    base_url = os.environ.get("PI_SERVICE_URL", "").strip()
    if not base_url:
        return None
    token = os.environ.get("PI_SERVICE_TOKEN") or None
    timeout_connect = float(os.environ.get("PI_SERVICE_TIMEOUT_CONNECT", "0.5"))
    timeout_read = float(os.environ.get("PI_SERVICE_TIMEOUT_READ", "1.0"))
    return PiServiceConfig(
        base_url=base_url.rstrip("/"),
        token=token,
        timeout_connect=timeout_connect,
        timeout_read=timeout_read,
    )


class PiServiceClient:
    def __init__(self, config: PiServiceConfig) -> None:
        self._config = config
        self._session = requests.Session()

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"
        if extra:
            headers.update(extra)
        return headers

    def _timeout(self) -> tuple[float, float]:
        return (self._config.timeout_connect, self._config.timeout_read)

    def get_status(self) -> dict[str, Any]:
        url = f"{self._config.base_url}/v1/status"
        resp = self._session.get(url, headers=self._headers(), timeout=self._timeout())
        resp.raise_for_status()
        return resp.json()

    def get_water_level(self) -> dict[str, Any]:
        url = f"{self._config.base_url}/v1/water-level"
        resp = self._session.get(url, headers=self._headers(), timeout=self._timeout())
        resp.raise_for_status()
        return resp.json()

    def start_watering(
        self,
        *,
        duration_sec: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self._config.base_url}/v1/watering/start"
        headers = self._headers(
            {"Idempotency-Key": idempotency_key} if idempotency_key else None
        )
        resp = self._session.post(
            url,
            json={"duration_sec": int(duration_sec)},
            headers=headers,
            timeout=self._timeout(),
        )
        resp.raise_for_status()
        return resp.json()

    def stop_watering(self) -> dict[str, Any]:
        url = f"{self._config.base_url}/v1/watering/stop"
        resp = self._session.post(url, headers=self._headers(), timeout=self._timeout())
        resp.raise_for_status()
        return resp.json()

    def get_gpio(self, *, verbose: bool = False) -> dict[str, Any]:
        url = f"{self._config.base_url}/v1/gpio"
        params = {"verbose": "1"} if verbose else None
        resp = self._session.get(
            url,
            params=params,
            headers=self._headers(),
            timeout=self._timeout(),
        )
        resp.raise_for_status()
        return resp.json()

