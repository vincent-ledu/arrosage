from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from domain.watering.ports import DeviceController


@dataclass(frozen=True, slots=True)
class WateringJob:
    job_id: str
    started_at: datetime
    duration_sec: int

    @property
    def scheduled_stop_at(self) -> datetime:
        return self.started_at + timedelta(seconds=self.duration_sec)


class PiWateringRuntime:
    def __init__(self, controller: DeviceController) -> None:
        self._controller = controller
        self._lock = threading.Lock()
        self._cancel_event: threading.Event | None = None
        self._job: WateringJob | None = None
        self._thread: threading.Thread | None = None
        self._last_error: str | None = None
        self._idempotency_key: str | None = None

    def start(self, duration_sec: int, *, idempotency_key: str | None = None) -> WateringJob:
        with self._lock:
            if (
                self._job is not None
                and idempotency_key
                and self._idempotency_key == idempotency_key
            ):
                return self._job
            if self._job is not None:
                raise RuntimeError("Watering is already in progress.")

            job = WateringJob(
                job_id=str(uuid.uuid4()),
                started_at=datetime.now(timezone.utc),
                duration_sec=duration_sec,
            )
            cancel_event = threading.Event()
            thread = threading.Thread(
                target=self._run_job,
                args=(job, cancel_event),
                daemon=True,
            )

            self._cancel_event = cancel_event
            self._job = job
            self._thread = thread
            self._last_error = None
            self._idempotency_key = idempotency_key

            thread.start()
            return job

    def stop(self) -> bool:
        with self._lock:
            if self._job is None:
                return False
            if self._cancel_event is not None:
                self._cancel_event.set()

        try:
            self._controller.close_water()
        finally:
            with self._lock:
                self._job = None
                self._cancel_event = None
                self._thread = None
                self._idempotency_key = None
        return True

    def status(self) -> dict:
        with self._lock:
            job = self._job
            last_error = self._last_error

        if job is None:
            return {
                "watering": False,
                "job_id": None,
                "since": None,
                "scheduled_stop_at": None,
                "remaining_sec": 0,
                "last_error": last_error,
            }

        now = datetime.now(timezone.utc)
        remaining = int((job.scheduled_stop_at - now).total_seconds())
        if remaining < 0:
            remaining = 0

        return {
            "watering": True,
            "job_id": job.job_id,
            "since": job.started_at.isoformat(),
            "scheduled_stop_at": job.scheduled_stop_at.isoformat(),
            "remaining_sec": remaining,
            "last_error": last_error,
        }

    def _run_job(self, job: WateringJob, cancel_event: threading.Event) -> None:
        try:
            self._controller.open_water()

            interval = 1
            elapsed = 0
            while elapsed < job.duration_sec:
                if cancel_event.is_set():
                    return
                if self._controller.get_level() * 25 <= 0:
                    with self._lock:
                        self._last_error = "Not enough water."
                    return
                time.sleep(interval)
                elapsed += interval
        except Exception as exc:  # pragma: no cover - defensive
            with self._lock:
                self._last_error = str(exc)
        finally:
            try:
                self._controller.close_water()
            finally:
                with self._lock:
                    if self._job and self._job.job_id == job.job_id:
                        self._job = None
                        self._cancel_event = None
                        self._thread = None
                        self._idempotency_key = None
