# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Clients for Open-Meteo's free weather APIs, keyless: the forecast and the historical weather, one class per host.

Open-Meteo serves each API from its own host: the forecast from ``api.open-meteo.com`` (``ForecastClient``) and the
historical weather (ERA5 reanalysis, from 1940) from ``archive-api.open-meteo.com`` (``ArchiveClient``). Each class has
its own base URL and calls only its own host; what they share (the rate budget, the models) is passed in or is a
module-level value, never a common base class. One method per documented read (the two ``GET``s of the API's OpenAPI
files, saved as ``docs_paths.json``), each returning its decoded model or raising a ``headgate.errors`` error.

**Terms** (https://open-meteo.com/en/terms, read 2026-10-27). The free API is for non-commercial use only (as Creative
Commons defines it: no subscriptions or advertising), at fewer than 10,000 calls a day, 5,000 an hour and 600 a minute
(300,000 a month, the pricing page adds), counted per IP address and application; Open-Meteo may block an application
or address that misuses it, without notice. The data is licensed CC BY 4.0, so whatever shows or republishes it credits
Open-Meteo; this client returns values as sent and adds no attribution of its own. Commercial use goes to the paid
``customer-`` hosts with an API key, which these clients do not call.

**One budget for both hosts.** The limits are counted per IP address across Open-Meteo's APIs, so the two clients
spend from one ``RateBudget``, passed to each as ``budget``: build it once with ``free_api_budget()`` and give it to
both. A ``429`` or a pause either host asks for then pauses both, and the pace is theirs together::

    budget = free_api_budget()
    async with (
        ForecastClient(user_agent=ua, budget=budget) as forecast,
        ArchiveClient(user_agent=ua, budget=budget) as archive,
    ):
        ...

**Pace: one request a second, at most five in flight**, for the two clients together: 60 a minute and 3,600 an hour,
under the minute and hour limits, so the clients never rely on the server to slow them down. Five is the free API's
documented queue: it processes one request at a time per client and answers ``429`` with no ``Retry-After`` to more
than five in flight. The day and month limits are the caller's to budget: at full pace they last under three hours. A
call costs more than one against the limits when it asks for much: ``max(1, V / 10 * max(1, D / 14))`` calls for ``V``
variables over ``D`` days (Open-Meteo's ``docs/api-rate-limiting.md``), which the pace, counting requests, does not
see. headgate's default retry policy (three attempts) re-sends a network failure, a ``5xx`` or a ``429``, each attempt
paced like any request. It waits a ``Retry-After`` of up to 30 seconds; the docs' example quota ``429`` carries
``Retry-After: 42``, which is not waited: the call raises ``RateLimitError`` with that delay as its ``retry_after``,
and the shared budget holds every later call, on either host, until the 42 seconds are over.

**Measured 2026-10-27** (12 requests in all, the terms and pricing pages included, at least 2.5 seconds apart, with
``User-Agent: headgate-client-skill-example/0.1 (+https://github.com/kelsayed17/headgate-client-skill)``, no key):

* Both reads answer ``200`` with ``Content-Type: application/json; charset=utf-8``. No response carried a rate-limit
  header (the ``X-RateLimit-*`` headers Open-Meteo's docs describe were added to its source the day before and were not
  yet sent), so the pace is this client's own.
* A coordinate out of range is ``400 {"reason":"Latitude must be in range of -90 to 90°. Given: 91.0.","error":true}``
  on both hosts (the archive sends the two keys the other way round). It raises ``UpstreamStatusError``, as do the
  other ``400``s measured: an unknown variable (``hourly=nonsense``: ``{"reason":"Invalid value: Cannot initialize …
  from invalid String value nonsense","error":true}``) and an archive date past today (``{"error":true,"reason":
  "Parameter 'start_date' is out of allowed range from 1940-01-01 to 2026-10-27"}``).
* The archive answered ``200`` with today's hours to a request with neither ``start_date`` nor ``end_date``, which the
  spec marks required; ``ArchiveParams`` requires them.
* Two comma-separated coordinates answer a JSON array, one object per location (the second with a ``location_id``),
  which ``Forecast`` does not decode: the params take one location.
* A repeated variable param (``current=temperature_2m&current=weather_code``) is read like a comma-separated one. The
  params take the comma-separated form the spec documents.

**Not measured:** a ``429`` (provoking one would break the terms; the shape above is the docs' example), a ``5xx``, and
a body with a gap (``null``) in a series.
"""

from typing import TYPE_CHECKING, Unpack

from headgate import AsyncBaseClient, HttpOptions, Rate, RateBudget
from headgate.pydantic import decoder

from examples.pydantic.open_meteo.models import ArchiveParams, Forecast, ForecastParams, Weather

if TYPE_CHECKING:
    import httpx2

FORECAST_URL = "https://api.open-meteo.com"
"""The forecast API's host. The path carries ``v1/``: the base URL carries no path."""

ARCHIVE_URL = "https://archive-api.open-meteo.com"
"""The historical weather API's host, another host from the forecast's: a class of its own."""

PACE = Rate.per_second(1)
"""One request a second, with no burst, for the two clients together."""

MAX_IN_FLIGHT = 5
"""The most requests the free API takes in flight from one client (IP address) before it answers ``429``."""

# Readers: built once, at import, where a bad declaration fails.
FORECAST = decoder(Forecast)
WEATHER = decoder(Weather)


def free_api_budget() -> RateBudget:
    """Return a budget for the free API's per-IP limits, to share between a ``ForecastClient`` and an ``ArchiveClient``.

    Build one per process (or per outgoing IP address) and pass it to every client of either host.
    """
    return RateBudget(PACE, max_in_flight=MAX_IN_FLIGHT)


class ForecastClient(AsyncBaseClient):
    """Read Open-Meteo's weather forecast for a location: up to 16 days ahead, and up to 92 days back (the spec's)."""

    def __init__(
        self, *, user_agent: str, budget: RateBudget, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Identify every request as ``user_agent``, which headgate sends first, before its own product tokens.

        ``budget`` is the rate budget shared with the other host's client (``free_api_budget()``). ``transport``
        replaces the network, as a test does.
        """
        super().__init__(
            base_url=FORECAST_URL,
            rate=budget,
            http=HttpOptions(
                user_agent=user_agent,
                transport=transport,
                headers={"Accept": "application/json"},
            ),
        )

    async def get_forecast(self, **params: Unpack[ForecastParams]) -> Forecast:
        """Return the forecast at ``params``' location, with the blocks and variables it names."""
        return await self.get("v1/forecast", params=params, expect=FORECAST)


class ArchiveClient(AsyncBaseClient):
    """Read Open-Meteo's historical weather for a location, from 1940-01-01 to today."""

    def __init__(
        self, *, user_agent: str, budget: RateBudget, transport: httpx2.AsyncBaseTransport | None = None
    ) -> None:
        """Identify every request as ``user_agent``, which headgate sends first, before its own product tokens.

        ``budget`` is the rate budget shared with the other host's client (``free_api_budget()``). ``transport``
        replaces the network, as a test does.
        """
        super().__init__(
            base_url=ARCHIVE_URL,
            rate=budget,
            http=HttpOptions(
                user_agent=user_agent,
                transport=transport,
                headers={"Accept": "application/json"},
            ),
        )

    async def get_archive(self, **params: Unpack[ArchiveParams]) -> Weather:
        """Return the weather at ``params``' location from ``start_date`` to ``end_date``, with the variables named."""
        return await self.get("v1/archive", params=params, expect=WEATHER)
