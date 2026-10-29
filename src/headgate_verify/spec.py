# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Writing the docs snapshot from the API's official OpenAPI or Swagger document: the ``headgate-snapshot`` command.

``headgate-snapshot write <docs_paths.json> <url or file>`` reads the spec and writes every operation in its
``paths`` (verb and path, ``operationId``, summary, request and response schema names, and whether a success answers
a JSON array or an object), recording the spec's URL as ``source``. ``headgate-snapshot refresh <docs_paths.json>``
reads ``source`` again and rewrites the endpoints, keeping ``reason``.

A source is a JSON or YAML document, or a docs page or script bundle that embeds the document as
``JSON.parse('…')`` string literals, as a Redoc page built ahead of time does; every embedded document found is
merged in. A URL is fetched with a ``User-Agent`` naming this tool (some docs servers refuse a generic one) and an
``Accept`` that prefers the OpenAPI media types, which a server that negotiates on them asks for. Only the vendor's
own spec belongs here: its docs site, its API host or its own source repository, never a community-maintained one.
"""

import argparse
import ast
import http
import http.client
import json
import re
import sys
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

import yaml

from headgate_verify.snapshot import DocsSnapshot, Endpoint, SnapshotError, dump_snapshot, load_snapshot

if TYPE_CHECKING:
    from collections.abc import Sequence

type Document = dict[str, Any]

HTTP_VERBS = ("get", "post", "put", "patch", "delete", "head")
"""The keys of an OpenAPI path item that are operations; the others (``parameters``, ``summary``) are not."""
USER_AGENT = f"headgate-snapshot/{version('headgate-verify')} (+https://github.com/kelsayed17/headgate-client-skill)"
ACCEPT = "application/vnd.oai.openapi+json, application/vnd.oai.openapi;q=0.9, application/json;q=0.8, */*;q=0.1"
_TIMEOUT = 120
_SCHEMA_REF = re.compile(r"#/(?:components/schemas|definitions)/([\w.-]+)")
_EMBEDDED = re.compile(r"JSON\.parse\('((?:[^'\\]|\\.)*)'\)", re.DOTALL)
_SUCCESS = ("200", "201")
_MAX_REFS = 10
_USAGE_ERROR = 2
_REDIRECTS = frozenset({301, 302, 303, 307, 308})
_MAX_REDIRECTS = 5


class SpecError(ValueError):
    """The source holds no OpenAPI or Swagger document, or cannot be read; the message says which."""


def parse_documents(raw: str) -> list[Document]:
    """Return the OpenAPI or Swagger documents in ``raw``: JSON, YAML, or ``JSON.parse('…')`` literals in a page."""
    if raw.lstrip().startswith("{"):
        documents: list[object] = [json.loads(raw)]
    else:
        embedded = [json.loads(ast.literal_eval(f"'{body}'")) for body in _EMBEDDED.findall(raw)]
        documents = embedded or [yaml.safe_load(raw)]
    found = [doc for doc in documents if isinstance(doc, dict) and isinstance(doc.get("paths"), dict)]
    if not found:
        msg = "the source holds no OpenAPI or Swagger document (no object with a paths table)"
        raise SpecError(msg)
    return found


def _resolve(schema: object, document: Document) -> Document:
    """Follow ``$ref`` links within ``document`` until a schema object is reached; ``{}`` when none is."""
    for _ in range(_MAX_REFS):
        if not isinstance(schema, dict) or "$ref" not in schema:
            break
        node: object = document
        for part in str(schema["$ref"]).lstrip("#/").split("/"):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        schema = node
    return schema if isinstance(schema, dict) else {}


def _success(operation: Document) -> Document:
    """Return the operation's first success response (``200``, else ``201``), or ``{}``."""
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return {}
    for code in _SUCCESS:
        found = responses.get(code, responses.get(int(code)))
        if isinstance(found, dict):
            return found
    return {}


def _success_schema(operation: Document) -> object:
    response = _success(operation)
    if "schema" in response:  # Swagger 2
        return response["schema"]
    content = response.get("content")
    if not isinstance(content, dict) or not content:
        return None
    media = content.get("application/json", next(iter(content.values())))
    return media.get("schema") if isinstance(media, dict) else None


def response_shape(operation: Document, document: Document) -> str:
    """Return ``array`` when a success answers a JSON array, ``object`` for an object, else ``""``."""
    schema = _resolve(_success_schema(operation), document)
    if schema.get("type") == "array" or "items" in schema:
        return "array"
    if schema.get("type") == "object" or "properties" in schema:
        return "object"
    return ""


def _first_ref(node: object) -> str:
    """Return the schema name of the first ``$ref`` anywhere in ``node``, or ``""``."""
    found = _SCHEMA_REF.search(json.dumps(node))
    return "" if found is None else str(found.group(1))


def request_schema(operation: Document) -> str:
    """Return the request body's schema name: an OpenAPI 3 ``requestBody`` or a Swagger 2 ``in: body`` parameter."""
    body = operation.get("requestBody")
    if body is None:
        parameters = operation.get("parameters")
        body = (
            [p for p in parameters if isinstance(p, dict) and p.get("in") == "body"]
            if isinstance(parameters, list)
            else []
        )
    return _first_ref(body)


def _text(value: object) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def endpoints(documents: Sequence[Document]) -> tuple[Endpoint, ...]:
    """Return every operation in the documents' ``paths``, sorted by ``(path, verb)``; a later repeat wins."""
    found: dict[tuple[str, str], Endpoint] = {}
    for document in documents:
        for path, item in document["paths"].items():
            for verb in HTTP_VERBS:
                operation = item.get(verb) if isinstance(item, dict) else None
                if isinstance(operation, dict):
                    found[path, verb.upper()] = Endpoint(
                        verb.upper(),
                        path,
                        operation_id=_text(operation.get("operationId")),
                        summary=_text(operation.get("summary")),
                        request_schema=request_schema(operation),
                        response_schema=_first_ref(_success(operation)),
                        response_shape=response_shape(operation, document),
                    )
    return tuple(found[key] for key in sorted(found))


def _fetch(url: str) -> tuple[str, str | None]:
    """Return the body at the ``https://`` ``url`` and its ``Date`` header, following up to five redirects."""
    for _ in range(_MAX_REDIRECTS + 1):
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname is None:
            msg = f"{url} is not an https URL"
            raise SpecError(msg)
        target = (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
        connection = http.client.HTTPSConnection(parts.netloc, timeout=_TIMEOUT)
        try:
            connection.request("GET", target, headers={"User-Agent": USER_AGENT, "Accept": ACCEPT})
            response = connection.getresponse()
            body = response.read()
            location = response.getheader("Location")
            if response.status in _REDIRECTS and location is not None:
                url = urljoin(url, location)
                continue
            if response.status != http.HTTPStatus.OK:
                msg = f"{url} answered {response.status} {response.reason}"
                raise SpecError(msg)
            charset = response.msg.get_content_charset() or "utf-8"
            return body.decode(charset), response.getheader("Date")
        finally:
            connection.close()
    msg = f"{url} redirected more than {_MAX_REDIRECTS} times"
    raise SpecError(msg)


def read_source(source: str) -> tuple[str, date]:
    """Return the text at ``source`` (an ``https://`` URL or a local file) and the day it was read, in UTC.

    A URL's day is its response's ``Date`` header, so it matches the dates a client's docstring records.
    """
    try:
        if not source.startswith("https://"):
            return Path(source).read_text(encoding="utf-8"), datetime.now(UTC).date()
        text, stamp = _fetch(source)
    except (OSError, UnicodeDecodeError, LookupError) as error:
        msg = f"{source} cannot be read: {error}"
        raise SpecError(msg) from error
    return text, datetime.now(UTC).date() if stamp is None else parsedate_to_datetime(stamp).astimezone(UTC).date()


def snapshot_of(source: str, reason: str | None = None) -> DocsSnapshot:
    """Return the snapshot of the spec at ``source``, recording ``source`` and ``reason``."""
    text, day = read_source(source)
    return DocsSnapshot(source, day, reason, endpoints(parse_documents(text)))


def write(target: Path, source: str) -> DocsSnapshot:
    """Write the snapshot of the spec at ``source`` to ``target``, keeping the ``reason`` a snapshot there has."""
    reason = load_snapshot(target).reason if target.exists() else None
    snapshot = snapshot_of(source, reason)
    target.write_text(dump_snapshot(snapshot), encoding="utf-8")
    return snapshot


def refresh(target: Path) -> DocsSnapshot:
    """Read the snapshot's ``source`` again and rewrite ``target``; raise ``SpecError`` when it has no source."""
    current = load_snapshot(target)
    if current.source is None:
        msg = f"{target} has source null, so there is nothing to read again"
        raise SpecError(msg)
    fresh = snapshot_of(current.source, current.reason)
    target.write_text(dump_snapshot(fresh), encoding="utf-8")
    return fresh


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``write`` or ``refresh``; return 0 when the snapshot was written, 2 when it could not be."""
    parser = argparse.ArgumentParser(prog="headgate-snapshot", description="Write docs_paths.json from an API spec.")
    commands = parser.add_subparsers(dest="command", required=True)
    write_command = commands.add_parser("write", help="write the snapshot from a spec URL or file")
    write_command.add_argument("target", type=Path, help="the docs_paths.json to write")
    write_command.add_argument("source", help="the vendor's official spec: an https URL or a local file")
    refresh_command = commands.add_parser("refresh", help="read each snapshot's source again and rewrite it")
    refresh_command.add_argument("targets", type=Path, nargs="+", help="the docs_paths.json files to refresh")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0) if isinstance(exit_.code, int) else _USAGE_ERROR
    source = str(args.source) if args.command == "write" else None
    targets = [Path(args.target)] if source is not None else [Path(target) for target in args.targets]
    failed = False
    for target in targets:
        try:
            snapshot = refresh(target) if source is None else write(target, source)
        except (SpecError, SnapshotError, json.JSONDecodeError, yaml.YAMLError) as error:
            sys.stderr.write(f"headgate-snapshot: {target}: {error}\n")
            failed = True
        else:
            sys.stderr.write(f"wrote {target}: {len(snapshot.endpoints)} endpoints from {snapshot.source}\n")
    return _USAGE_ERROR if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
