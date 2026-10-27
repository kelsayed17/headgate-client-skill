# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The method-name test helper: a client's ``test_method_names.py`` is ``assert check_names(...) == []``.

A read is named ``get_`` plus the literal segments of its path (``endpoint_name``), and every method is compared
with the docs snapshot saved beside the client as ``docs_paths.json``::

    {"source": "https://…/openapi.json" | null, "retrieved": "YYYY-MM-DD", "reason": str | null,
     "endpoints": [{"verb": "GET", "path": "/v1/foo/{id}"}, …]}

``endpoints`` is sorted by ``(path, verb)`` with no repeats, ``reason`` is required when ``source`` is null (the API
publishes no reference), and no other key is allowed. The schema is validated by hand here: it is four keys, and its
sort order and the reason-when-null condition would need code beside any schema library anyway, so a runtime
dependency would buy nothing.

The client is read statically with ast-grep-py and never imported (``client_endpoints``). A client path is relative
to the client's base URL, so it matches a documented path when, after normalising both (strip ``/`` at either end,
every ``{name}`` hole compares as ``{}``, the verb upper-cased), it equals the documented path or is a suffix of it on
a segment boundary (ruling R16). A method matching more than one documented path is a problem, never a pick.
"""

import itertools
import json
import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from ast_grep_py import SgRoot

from headgate_verify.config import Config

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

    from ast_grep_py import SgNode

DEFAULT_FILLER: frozenset[str] = Config().filler_words
"""The filler words dropped from a path when no other set is given: the verifier's default ``filler_words``."""

_VERSION = re.compile(r"^v\d+$|^vX$")
_HOLE = re.compile(r"\{[^{}]*\}")
_WORD_SPLIT = re.compile(r"[-_.]|(?<=[a-z0-9])(?=[A-Z])")
_VERB = re.compile(r"^[A-Z]+$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_KEYS = frozenset({"source", "retrieved", "reason", "endpoints"})
_ALL_KEYS = "source, retrieved, reason and endpoints"
_VERBS = {"get": "GET", "post": "POST", "put": "PUT", "patch": "PATCH", "delete": "DELETE", "head": "HEAD"}
_GET = "GET"


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


# endpoint_name


def endpoint_name(path: str, *, filler: frozenset[str] = DEFAULT_FILLER, prefix: str = "get_") -> str:
    """Return the method name of a read of ``path``: ``prefix`` plus its literal words, joined by ``_``.

    Empty, ``{param}``, version (``v1``, ``vX``) and ``filler`` segments are dropped; a hole inside a segment is
    removed; each remaining segment splits on ``-``, ``_``, ``.`` and a lower-to-upper camelCase boundary (no split
    inside an all-caps run: ``CNMSshvol`` is one word); the words are lower-cased. A path with no word gives
    ``prefix`` without its trailing ``_``.
    """
    words: list[str] = []
    for segment in path.split("/"):
        if not segment or _VERSION.match(segment) or segment in filler or _HOLE.fullmatch(segment):
            continue
        words.extend(word.lower() for word in _WORD_SPLIT.split(_HOLE.sub("", segment)) if word)
    return prefix + "_".join(words) if words else prefix.rstrip("_")


# load_snapshot


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


# client_endpoints


@dataclass(frozen=True)
class _Module:
    """The parts of ``client.py`` the endpoint reader resolves names against."""

    constants: dict[str, SgNode]
    functions: dict[str, SgNode]


def _module(root: SgNode) -> _Module:
    constants: dict[str, SgNode] = {}
    functions: dict[str, SgNode] = {}
    for statement in root.children():
        node = statement.field("definition") if statement.kind() == "decorated_definition" else statement
        if node is None:
            continue
        if node.kind() == "function_definition" and (name := node.field("name")) is not None:
            functions[name.text()] = node
        elif node.kind() == "expression_statement" and (assignment := node.child(0)) is not None:
            left, right = assignment.field("left"), assignment.field("right")
            if (
                assignment.kind() == "assignment"
                and left is not None
                and right is not None
                and left.kind() == "identifier"
                and right.kind() == "string"
            ):
                constants[left.text()] = right
    return _Module(constants, functions)


def _string(node: SgNode, env: Mapping[str, SgNode], module: _Module) -> str | None:
    """Return the text of a plain or t-string literal, each hole inlined when it names a string, else ``{name}``."""
    start = node.child(0)
    if start is None or any(letter in start.text().lower() for letter in "fb"):
        return None
    parts: list[str] = []
    for child in node.children()[1:-1]:
        if child.kind() != "interpolation":
            parts.append(child.text())
            continue
        expression = child.named_children()[0]
        inlined = _path(expression, env, module) if expression.kind() == "identifier" else None
        parts.append(f"{{{expression.text()}}}" if inlined is None else inlined)
    return "".join(parts)


def _path(node: SgNode, env: Mapping[str, SgNode], module: _Module) -> str | None:
    """Return the path ``node`` spells: a string, or a name bound in ``env`` or to a module-level string."""
    if node.kind() == "string":
        return _string(node, env, module)
    if node.kind() == "identifier":
        bound = env.get(node.text())
        if bound is not None:
            return _path(bound, {}, module)
        constant = module.constants.get(node.text())
        if constant is not None:
            return _string(constant, {}, module)
    return None


def _arguments(call: SgNode) -> tuple[list[SgNode], dict[str, SgNode]]:
    positional: list[SgNode] = []
    keywords: dict[str, SgNode] = {}
    arguments = call.field("arguments")
    for argument in [] if arguments is None else arguments.named_children():
        if argument.kind() == "keyword_argument":
            name, value = argument.field("name"), argument.field("value")
            if name is not None and value is not None:
                keywords[name.text()] = value
        elif argument.kind() not in {"comment", "list_splat", "dictionary_splat"}:
            positional.append(argument)
    return positional, keywords


def _parameters(function: SgNode) -> list[str]:
    parameters = function.field("parameters")
    names: list[str] = []
    for parameter in [] if parameters is None else parameters.named_children():
        if parameter.kind() == "identifier":
            names.append(parameter.text())
        elif parameter.kind() == "typed_parameter" and (name := parameter.child(0)) is not None:
            names.append(name.text())
        elif parameter.kind() in {"default_parameter", "typed_default_parameter"}:
            name = parameter.field("name")
            if name is not None:
                names.append(name.text())
    return names


def _verb_call(call: SgNode, receiver: str, env: Mapping[str, SgNode], module: _Module) -> Endpoint | None:
    """Return the endpoint of ``<receiver>.<verb>(path, …)``, or None when ``call`` is not one or is unreadable."""
    function = call.field("function")
    if function is None or function.kind() != "attribute":
        return None
    target, attribute = function.field("object"), function.field("attribute")
    if target is None or attribute is None or target.text() != receiver:
        return None
    positional, keywords = _arguments(call)
    route = keywords.get("url", positional[0] if positional else None)
    name = attribute.text()
    if name in _VERBS:
        verb: str | None = _VERBS[name]
    elif name == "paginate":
        verb = _GET
    elif name == "stream":
        method = keywords.get("method")
        verb = _GET if method is None else _path(method, env, module)
    else:
        return None
    path = None if route is None else _path(route, env, module)
    return None if verb is None or path is None else Endpoint(verb.upper(), path)


def _first_verb_call(body: SgNode, receiver: str, env: Mapping[str, SgNode], module: _Module) -> Endpoint | None:
    for call in body.find_all(kind="call"):
        endpoint = _verb_call(call, receiver, env, module)
        if endpoint is not None:
            return endpoint
    return None


def _leg(call: SgNode, methods: Mapping[str, SgNode], module: _Module) -> tuple[SgNode, list[str], str] | None:
    """Return ``(leg, parameter names the caller's arguments bind, receiver)`` when ``call`` delegates to a leg."""
    function = call.field("function")
    if function is None:
        return None
    if function.kind() == "attribute" and (target := function.field("object")) is not None and target.text() == "self":
        attribute = function.field("attribute")
        leg = None if attribute is None else methods.get(attribute.text())
        return None if leg is None else (leg, _parameters(leg)[1:], "self")
    if function.kind() == "identifier" and (leg := module.functions.get(function.text())) is not None:
        names = _parameters(leg)
        return None if not names else (leg, names, names[0])
    return None


def _delegated(body: SgNode, methods: Mapping[str, SgNode], module: _Module) -> Endpoint | None:
    """Return the endpoint of the first one-level delegation in ``body`` to a sibling method or module function."""
    for call in body.find_all(kind="call"):
        found = _leg(call, methods, module)
        if found is None:
            continue
        leg, names, receiver = found
        positional, keywords = _arguments(call)
        env = dict(zip(names, positional, strict=False)) | {k: v for k, v in keywords.items() if k in names}
        leg_body = leg.field("body")
        return None if leg_body is None else _first_verb_call(leg_body, receiver, env, module)
    return None


def _class_methods(cls: SgNode) -> dict[str, SgNode]:
    body = cls.field("body")
    methods: dict[str, SgNode] = {}
    for statement in [] if body is None else body.named_children():
        node = statement.field("definition") if statement.kind() == "decorated_definition" else statement
        if node is not None and node.kind() == "function_definition" and (name := node.field("name")) is not None:
            methods[name.text()] = node
    return methods


def client_endpoints(client_module: Path) -> dict[str, Endpoint]:
    """Return the verb and path of each public method of each class in ``client_module``, read statically.

    A method's endpoint is its first ``self.<verb>(path, …)`` call (``get``, ``post``, ``put``, ``patch``,
    ``delete``, ``head``; ``paginate`` is GET; ``stream`` is its literal ``method=``, GET by default). The path is a
    string or t-string literal, or a name bound to a module-level one; a t-string hole naming a module-level string
    is inlined, and any other hole becomes ``{expression}`` without its conversion or format spec. A method that
    instead delegates to a sibling method or a module-level function is resolved one level: the leg's verb call is
    read with the leg's parameters bound to the caller's arguments. A method whose path is anything else (a
    parameter of the public method, a call, an f-string, a concatenation) or that delegates twice is left out.
    """
    root = SgRoot(client_module.read_text(encoding="utf-8"), "python").root()
    module = _module(root)
    endpoints: dict[str, Endpoint] = {}
    for cls in root.find_all(kind="class_definition"):
        methods = _class_methods(cls)
        for name, method in methods.items():
            body = method.field("body")
            if name.startswith("_") or body is None:
                continue
            endpoint = _first_verb_call(body, "self", {}, module) or _delegated(body, methods, module)
            if endpoint is not None:
                endpoints[name] = endpoint
    return endpoints


# check_names


def _segments(path: str) -> tuple[str, ...]:
    stripped = _HOLE.sub("{}", path.strip("/"))
    return tuple(stripped.split("/")) if stripped else ()


def _matches(client: tuple[str, ...], documented: tuple[str, ...]) -> bool:
    return len(client) <= len(documented) and documented[len(documented) - len(client) :] == client


def _name(segments: tuple[str, ...], universe: Collection[tuple[str, ...]], filler: frozenset[str]) -> str:
    """Return the path's name, its last word singular when it is an item endpoint whose list shares the name."""
    name = endpoint_name("/".join(segments), filler=filler)
    is_item = bool(segments) and segments[-1] == "{}" and segments[:-1] in universe
    if is_item and endpoint_name("/".join(segments[:-1]), filler=filler) == name:
        return name.removesuffix("s")
    return name


@dataclass
class _Comparison:
    """What comparing the methods with the documented endpoints found."""

    problems: list[str]
    matched: dict[str, list[Endpoint]]
    prefixes: set[tuple[str, ...]]


def _compare(methods: Mapping[str, Endpoint], snapshot: DocsSnapshot, file: str) -> _Comparison:
    found = _Comparison([], {}, set())
    documented = [(endpoint, _segments(endpoint.path)) for endpoint in snapshot.endpoints]
    for name, endpoint in sorted(methods.items()):
        client = _segments(endpoint.path)
        candidates = [(doc, segs) for doc, segs in documented if doc.verb == endpoint.verb and _matches(client, segs)]
        where = f"{name} calls {endpoint.verb} {endpoint.path}"
        if not candidates:
            found.problems.append(f"{where}, which is not in the snapshot {file}")
        elif len(candidates) > 1:
            listed = ", ".join(f"{doc.verb} {doc.path}" for doc, _ in candidates)
            found.problems.append(f"{where}, which matches more than one documented path ({listed}); make it match one")
            found.matched[name] = [doc for doc, _ in candidates]
        else:
            ((doc, segs),) = candidates
            found.matched[name] = [doc]
            found.prefixes.add(segs[: len(segs) - len(client)])
    return found


def _strip_prefix(segments: tuple[str, ...], prefixes: Collection[tuple[str, ...]]) -> tuple[str, ...]:
    for prefix in sorted(prefixes, key=len, reverse=True):
        if segments[: len(prefix)] == prefix:
            return segments[len(prefix) :]
    return segments


def _unknown_names(label: str, names: Collection[str], methods: Mapping[str, Endpoint]) -> list[str]:
    return [
        f"{label} names {name}, which is not a public method of the client with a path read statically"
        for name in sorted(set(names) - set(methods))
    ]


def check_names(  # noqa: PLR0913 -- the documented signature: two files and four keyword-only knobs
    client_module: Path,
    snapshot: Path,
    *,
    overrides: Mapping[str, str] = {},
    exempt_writes: Collection[str] = (),
    post_reads: Collection[str] = (),
    filler: frozenset[str] | None = None,
) -> list[str]:
    """Return one sentence per naming problem of ``client_module`` against the ``snapshot`` file; ``[]`` is clean.

    A read is a GET method or a method named in ``post_reads``; its name must be
    ``overrides.get(name_from_path, name_from_path)``, where ``name_from_path`` is ``endpoint_name`` of its path,
    singularised when the read is an item endpoint (its list's path plus one trailing ``{param}``) whose list endpoint
    shares that name. Also reported: a documented GET with no method; a method whose endpoint the snapshot does not
    list, or lists more than once (both skipped when ``source`` is null); an override key no endpoint is named
    (stale); a non-GET method in neither ``exempt_writes`` nor ``post_reads``; a name in ``exempt_writes`` or
    ``post_reads`` that is no method. Raise ``SnapshotError`` when the snapshot breaks its schema.
    """
    docs = load_snapshot(snapshot)
    filler = DEFAULT_FILLER if filler is None else filler
    methods = client_endpoints(client_module)
    problems = [
        f"{name} sends {endpoint.verb} {endpoint.path}; list it in exempt_writes, or in post_reads if it reads"
        for name, endpoint in sorted(methods.items())
        if endpoint.verb != _GET and name not in exempt_writes and name not in post_reads
    ]
    problems += _unknown_names("exempt_writes", exempt_writes, methods)
    problems += _unknown_names("post_reads", post_reads, methods)
    reads = {name: endpoint for name, endpoint in methods.items() if endpoint.verb == _GET or name in post_reads}
    universe = {_segments(endpoint.path) for endpoint in reads.values()}
    if docs.source is not None:
        found = _compare(methods, docs, snapshot.name)
        problems += found.problems
        matched = {doc for docs_of_method in found.matched.values() for doc in docs_of_method}
        problems += [
            f"the documented read {endpoint.verb} {endpoint.path} has no method"
            for endpoint in docs.endpoints
            if endpoint.verb == _GET and endpoint not in matched
        ]
        documented_reads = {endpoint for endpoint in docs.endpoints if endpoint.verb == _GET} | {
            doc for name in post_reads for doc in found.matched.get(name, [])
        }
        universe |= {_strip_prefix(_segments(endpoint.path), found.prefixes) for endpoint in documented_reads}
    for name, endpoint in sorted(reads.items()):
        from_path = _name(_segments(endpoint.path), universe, filler)
        expected = overrides.get(from_path, from_path)
        if name != expected:
            problems.append(
                f"{name} reads {endpoint.verb} {endpoint.path} and should be named {expected} "
                "(or add an override with a reason)"
            )
    names = {_name(segments, universe, filler) for segments in universe}
    problems += [
        f"the override {key!r} -> {value!r} is stale: no endpoint is named {key}"
        for key, value in sorted(overrides.items())
        if key not in names
    ]
    return problems
