# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The docs snapshot: the API's documented endpoints, saved beside a client as ``docs_paths.json``.

The file reads::

    {"source": "https://…/openapi.json" | null, "retrieved": "YYYY-MM-DD", "reason": str | null,
     "endpoints": [{"verb": "GET", "path": "/v1/foo/{id}", "operation_id": "getFoo", "summary": "Get a Foo",
                    "request_schema": "", "response_schema": "Foo", "response_shape": "object"}, …]}

``endpoints`` is sorted by ``(path, verb)`` with no repeats, ``reason`` is required when ``source`` is null (the API
publishes no reference), and no other key is allowed. An endpoint needs ``verb`` and ``path``; the five operation
details are what an OpenAPI or Swagger document says of it (``headgate_verify.spec`` writes them), each a string and
``""`` when absent, and ``response_shape`` is ``array``, ``object`` or ``""``. The schema is validated by hand here:
its sort order and the reason-when-null condition would need code beside any schema library anyway, so a runtime
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
_DETAILS = ("operation_id", "summary", "request_schema", "response_schema", "response_shape")
_ENDPOINT_KEYS = frozenset({"verb", "path", *_DETAILS})
_SHAPES = frozenset({"array", "object", ""})


class SnapshotError(ValueError):
    """``docs_paths.json`` is not valid JSON or does not follow the snapshot schema; the message says how."""


@dataclass(frozen=True)
class Endpoint:
    """One HTTP verb on one path, with what the API's spec says of it (each ``""`` when it says nothing)."""

    verb: str
    path: str
    operation_id: str = ""
    """The spec's ``operationId``."""
    summary: str = ""
    """The spec's one-line ``summary``, its whitespace collapsed."""
    request_schema: str = ""
    """The name of the request body's schema."""
    response_schema: str = ""
    """The name of the first success response's schema."""
    response_shape: str = ""
    """``array`` when a success answers a JSON array, ``object`` for an object, ``""`` when the spec does not say."""


@dataclass(frozen=True)
class DocsSnapshot:
    """The API's documented surface, as saved in ``docs_paths.json``."""

    source: str | None
    retrieved: date
    reason: str | None
    endpoints: tuple[Endpoint, ...]


def _endpoint(index: int, item: object) -> Endpoint:
    if not isinstance(item, dict) or not {"verb", "path"} <= set(item) <= _ENDPOINT_KEYS:
        msg = f"endpoints[{index}] must be an object with the keys verb and path, and only {', '.join(_DETAILS)} beside"
        raise SnapshotError(msg)
    verb, route = item["verb"], item["path"]
    if not isinstance(verb, str) or not _VERB.match(verb):
        msg = f"endpoints[{index}].verb must be an upper-case HTTP verb such as GET; got {verb!r}"
        raise SnapshotError(msg)
    if not isinstance(route, str):
        msg = f"endpoints[{index}].path must be a string; got {route!r}"
        raise SnapshotError(msg)
    details: dict[str, str] = {}
    for key in _DETAILS:
        value = item.get(key, "")
        if not isinstance(value, str):
            msg = f"endpoints[{index}].{key} must be a string; got {value!r}"
            raise SnapshotError(msg)
        details[key] = value
    if details["response_shape"] not in _SHAPES:
        msg = f"endpoints[{index}].response_shape must be array, object or empty; got {details['response_shape']!r}"
        raise SnapshotError(msg)
    return Endpoint(verb, route, **details)


def _endpoints(value: object) -> tuple[Endpoint, ...]:
    if not isinstance(value, list):
        msg = "endpoints must be a list of endpoint objects"
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


def dump_snapshot(snapshot: DocsSnapshot) -> str:
    """Return ``snapshot`` as the text of a ``docs_paths.json``, which ``load_snapshot`` reads back unchanged."""
    data = {
        "source": snapshot.source,
        "retrieved": snapshot.retrieved.isoformat(),
        "reason": snapshot.reason,
        "endpoints": [
            {"verb": e.verb, "path": e.path, **{key: getattr(e, key) for key in _DETAILS}} for e in snapshot.endpoints
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
