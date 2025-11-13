from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import List, Mapping, Sequence

from domain.weather.ports import ForecastCache, ForecastProvider


class ForecastService:
    def __init__(
        self,
        provider: ForecastProvider,
        cache: ForecastCache,
        ttl: timedelta = timedelta(minutes=30),
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._ttl = ttl

    def get_partday_forecast(
        self, latitude: float, longitude: float
    ) -> tuple[List[Mapping], bool]:
        cached = self._cache.get_partday_forecast()
        if cached and self._is_list_fresh(cached):
            return cached, True

        raw = list(self._provider.fetch_partday_forecast(latitude, longitude))
        self._cache.store_partday_forecast(raw)
        return raw, False

    def get_daily_minmax_precip(
        self, target_date: date, latitude: float, longitude: float
    ) -> tuple[Mapping, bool]:
        cached = self._cache.get_daily_forecast(target_date)
        if cached and self._is_entry_fresh(cached):
            return cached, True

        raw = self._provider.fetch_daily_forecast(latitude, longitude)
        self._cache.store_daily_forecast(
            target_date,
            raw["temperature_2m_min"],
            raw["temperature_2m_max"],
            raw["precipitation_sum"],
        )
        refreshed = self._cache.get_daily_forecast(target_date)
        return (refreshed or raw), False

    def _is_list_fresh(self, entries: Sequence[Mapping]) -> bool:
        if not entries:
            return False
        updated_at = entries[0].get("updated_at")
        return self._is_recent(updated_at)

    def _is_entry_fresh(self, entry: Mapping) -> bool:
        return self._is_recent(entry.get("updated_at"))

    def _is_recent(self, updated_at_value) -> bool:
        if not updated_at_value:
            return False
        if isinstance(updated_at_value, datetime):
            updated_at = updated_at_value
        else:
            updated_at = datetime.strptime(str(updated_at_value), "%Y-%m-%d %H:%M:%S")

        # Les horodatages stockés en base sont normalisés en UTC.
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        else:
            updated_at = updated_at.astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        if updated_at > now:
            # Si les données semblent dater du futur (ex : ancien enregistrement en timezone locale),
            # on force un rafraîchissement pour corriger la dérive.
            return False
        return now < updated_at + self._ttl

    def set_ttl(self, ttl: timedelta) -> None:
        self._ttl = ttl
