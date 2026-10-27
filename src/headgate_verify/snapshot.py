# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The docs snapshot: the API's documented endpoints, saved beside a client as ``docs_paths.json``.

The file reads::

    {"source": "https://…/openapi.json" | null, "retrieved": "YYYY-MM-DD", "reason": str | null,
     "endpoints": [{"verb": "GET", "path": "/v1/foo/{id}"}, …]}

``endpoints`` is sorted by ``(path, verb)`` with no repeats, ``reason`` is required when ``source`` is null (the API
publishes no reference), and no other key is allowed. The schema is validated by hand here: it is four keys, and its
sort order and the reason-when-null condition would need code beside any schema library anyway, so a runtime
dependency would buy nothing.
"""

import itertools
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_VERB = re.compile(r"^[A-Z]+$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_KEYS = frozenset({"source", "retrieved", "reason", "endpoints"})
_ALL_KEYS = "source, retrieved, reason and endpoints"


class SnapshotError(ValueError):
    """``docs_paths.json`` is not valid JSON or does not follow the snapshot schema; the message says how."""


@dataclass(frozen=True)
class Endpoint:
    """One HTTP verb on one path."""

    verb: str
    path: str


@dataclass(frozen=True)
class DocsSnapshot:
    """The API's documented surface, as saved in ``docs_paths.json``."""

    source: str | None
    retrieved: date
    reason: str | None
    endpoints: tuple[Endpoint, ...]


def _endpoint(index: int, item: object) -> Endpoint:
    if not isinstance(item, dict) or set(item) != {"verb", "path"}:
        msg = f"endpoints[{index}] must be an object with exactly the keys verb and path"
        raise SnapshotError(msg)
    verb, route = item["verb"], item["path"]
    if not isinstance(verb, str) or not _VERB.match(verb):
        msg = f"endpoints[{index}].verb must be an upper-case HTTP verb such as GET; got {verb!r}"
        raise SnapshotError(msg)
    if not isinstance(route, str):
        msg = f"endpoints[{index}].path must be a string; got {route!r}"
        raise SnapshotError(msg)
    return Endpoint(verb, route)


def _endpoints(value: object) -> tuple[Endpoint, ...]:
    if not isinstance(value, list):
        msg = "endpoints must be a list of {verb, path} objects"
        raise SnapshotError(msg)
    endpoints = tuple(_endpoint(index, item) for index, item in enumerate(value))
    keys = [(endpoint.path, endpoint.verb) for endpoint in endpoints]
    for before, after in itertools.pairwise(keys):
        if before == after:
            msg = f"endpoints lists {after[1]} {after[0]} twice"
            raise SnapshotError(msg)
        if before > after:
            msg = f"endpoints must be sorted by (path, verb); {after[1]} {after[0]} comes after {before[1]} {before[0]}"
            raise SnapshotError(msg)
    return endpoints


def _optional_text(data: dict[str, object], key: str) -> str | None:
    value = data[key]
    if value is not None and (not isinstance(value, str) or not value.strip()):
        msg = f"{key} must be a non-empty string or null; got {value!r}"
        raise SnapshotError(msg)
    return value


def _retrieved(value: object) -> date:
    if not isinstance(value, str) or not _DATE.match(value):
        msg = f"retrieved must be a YYYY-MM-DD date; got {value!r}"
        raise SnapshotError(msg)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        msg = f"retrieved must be a YYYY-MM-DD date; {value!r} is not one ({error})"
        raise SnapshotError(msg) from error


def load_snapshot(path: Path) -> DocsSnapshot:
    """Return the snapshot in ``path``; raise ``SnapshotError`` when it is unreadable or breaks the schema."""
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        msg = f"the file cannot be read: {error}"
        raise SnapshotError(msg) from error
    except json.JSONDecodeError as error:
        msg = f"the file is not valid JSON: {error}"
        raise SnapshotError(msg) from error
    if not isinstance(data, dict):
        msg = f"the snapshot must be a JSON object with the keys {_ALL_KEYS}"
        raise SnapshotError(msg)
    if missing := sorted(_KEYS - set(data)):
        msg = f"the snapshot lacks the key(s) {', '.join(missing)}; every snapshot has {_ALL_KEYS}"
        raise SnapshotError(msg)
    if unknown := sorted(set(data) - _KEYS):
        msg = f"the snapshot has the unknown key(s) {', '.join(unknown)}; it has only {_ALL_KEYS}"
        raise SnapshotError(msg)
    source, reason = _optional_text(data, "source"), _optional_text(data, "reason")
    if source is None and reason is None:
        msg = "the snapshot has source null and no reason; say why the API's reference cannot be saved"
        raise SnapshotError(msg)
    return DocsSnapshot(source, _retrieved(data["retrieved"]), reason, _endpoints(data["endpoints"]))
