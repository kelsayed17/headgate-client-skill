# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Open-Meteo's wire shapes: frozen pydantic models with the API's own field names, and each endpoint's params.

Modelled on the two OpenAPI files the docs snapshot names (``forecast.yml`` and ``historical-weather.yml``, read
2026-10-27) and checked against the bodies recorded the same day (``tests/fixtures/``). Both hosts answer one shape:
the grid cell's location, then one block per kind of series asked for (``hourly``, ``daily``; on the forecast also
``current`` and ``minutely_15``), each with a ``<block>_units`` map beside it.

* **A block is present only when asked for.** A request naming no ``daily`` variable gets no ``daily`` key, so every
  block defaults to ``None``; the location fields are always sent.
* **A block's variables are the ones asked for.** The spec lists hundreds (355 hourly on the forecast) and a block
  holds only the requested ones, so a block is a map from each name (``time`` too) to its values, not a model with a
  field per variable. Values keep their JSON type: a temperature is a ``float``, a ``weather_code`` or
  ``precipitation_probability`` an ``int``, a ``time`` or ``sunrise`` a ``Time``, a gap ``None``.
* **Times are local and carry no offset.** In the default ``timeformat=iso8601`` a time is ``"2026-10-27T07:00"`` (a
  day is ``"2026-10-27"``) in the ``timezone`` asked for, GMT unless one is; add ``utc_offset_seconds`` for UTC. With
  ``timeformat=unixtime`` each time is an ``int`` of seconds since the epoch, UTC. ``Time`` takes either, as sent.

Decoded strictly (``headgate.pydantic``'s default): a JSON string where a location field declares a number fails the
decode.

**Not measured:** a ``None`` inside a series (no recorded body had a gap) and any block or variable not in the
fixtures; their types are the spec's.
"""

from typing import Literal, Required, TypedDict

from pydantic import BaseModel, ConfigDict

type Time = str | int
"""A time as sent: ISO 8601 local time (``"2026-10-27T07:00"``) or day, or Unix seconds with ``timeformat=unixtime``."""

type Value = int | float | Time | None
"""One value of a variable: a number, a time (``sunrise``, ``sunset``), or ``None`` where the model has no data."""

type Series = dict[str, list[Value]]
"""One block of series (``hourly``, ``daily``, ``minutely_15``): ``time`` and each variable asked for, to its values.

``time`` holds one ``Time`` per step; each variable holds one value per step, in the same order.
"""

type Current = dict[str, Value]
"""The ``current`` block: ``time``, ``interval`` (the seconds it covers, up to ``time``) and each variable's value."""


# Responses


class Weather(BaseModel):
    """A historical weather answer, and the part of a forecast answer the two hosts share.

    ``latitude``, ``longitude`` and ``elevation`` are the grid cell's, not the ones asked for (``52.52, 13.41`` was
    answered ``52.512604, 13.419517`` by the forecast and ``52.54833, 13.407822`` by the archive). Each ``*_units`` map
    names each variable's unit (``"°C"``, ``"%"``, ``"iso8601"`` for a time).
    """

    model_config = ConfigDict(frozen=True)

    latitude: float
    longitude: float
    elevation: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    hourly: Series | None = None
    hourly_units: dict[str, str] | None = None
    daily: Series | None = None
    daily_units: dict[str, str] | None = None


class Forecast(Weather):
    """A forecast answer: the shared blocks, plus the current conditions and the 15-minute series."""

    current: Current | None = None
    current_units: dict[str, str] | None = None
    minutely_15: Series | None = None
    minutely_15_units: dict[str, str] | None = None


# Query parameters

type TemperatureUnit = Literal["celsius", "fahrenheit"]
type WindSpeedUnit = Literal["kmh", "ms", "mph", "kn"]
type PrecipitationUnit = Literal["mm", "inch"]
type TimeFormat = Literal["iso8601", "unixtime"]
type CellSelection = Literal["land", "sea", "nearest"]


class WeatherParams(TypedDict, total=False):
    """The params both endpoints take, as the spec lists them; the defaults are the server's.

    One location per call: ``latitude`` and ``longitude`` are numbers here. The API also takes comma-separated lists
    of both, and then answers a JSON array with one object per location, which these models do not decode.
    ``hourly``, ``daily`` and ``models`` are comma-separated names (``"temperature_2m,precipitation"``), as the spec
    describes them. ``timezone`` is an IANA name, or ``"auto"`` for the location's own; the default is GMT. The spec's
    ``apikey`` is left out: it belongs to the paid ``customer-`` hosts, which these clients do not call.

    A request for many variables or a long range counts as more than one call against the limits (the client's module
    docstring gives the formula).
    """

    latitude: Required[float]
    longitude: Required[float]
    hourly: str
    daily: str
    elevation: float
    temperature_unit: TemperatureUnit
    wind_speed_unit: WindSpeedUnit
    precipitation_unit: PrecipitationUnit
    timeformat: TimeFormat
    timezone: str
    past_days: int
    forecast_days: int
    past_hours: int
    forecast_hours: int
    tilt: float
    azimuth: float
    cell_selection: CellSelection
    models: str


class ForecastParams(WeatherParams, total=False):
    """Params of ``GET /v1/forecast``: the shared ones, the forecast's two extra blocks and an optional date range.

    ``current`` and ``minutely_15`` are comma-separated variable names. ``start_date`` and ``end_date`` are
    ``yyyy-mm-dd`` and replace ``past_days`` / ``forecast_days``.
    """

    current: str
    minutely_15: str
    start_date: str
    end_date: str


class ArchiveParams(WeatherParams, total=False):
    """Params of ``GET /v1/archive``: the shared ones and the date range, ``yyyy-mm-dd``, from 1940-01-01 to today.

    The spec marks both dates required. The server did not enforce it (2026-10-27: a request with neither answered
    ``200`` with today's hours), but they are required here, as documented.
    """

    start_date: Required[str]
    end_date: Required[str]
