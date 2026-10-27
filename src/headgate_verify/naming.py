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

A public method that sends a request whose path is not a string, t-string or module-level constant (or a one-level
delegate to one) is reported by name (``unreadable_methods``), never dropped in silence, and a documented read with no
method says how many such methods there are. When the snapshot has a source and a method matches exactly one
documented endpoint, its expected name comes from the documented path, which carries any prefix the base URL holds;
otherwise from the client's own path (ruling R18). An ``overrides`` key is a derived name or ``"VERB path"`` (the path
normalised as above); a ``"VERB path"`` key wins over a name key, either is reported when stale, and two read paths
that still derive one name are reported with the ``"VERB path"`` key that would separate them (ruling R17).
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


_REQUESTS = frozenset({*_VERBS, "paginate", "stream"})


@dataclass(frozen=True)
class _Request:
    """A method's request: its endpoint, None when the path cannot be read, and the call that sends it."""

    endpoint: Endpoint | None
    call: str


def _request_name(call: SgNode, receiver: str) -> str | None:
    """Return ``get``, ``paginate``, … when ``call`` is ``<receiver>.<that>(…)``, else None."""
    function = call.field("function")
    if function is None or function.kind() != "attribute":
        return None
    target, attribute = function.field("object"), function.field("attribute")
    if target is None or attribute is None or target.text() != receiver or attribute.text() not in _REQUESTS:
        return None
    return attribute.text()


def _read_request(call: SgNode, name: str, env: Mapping[str, SgNode], module: _Module) -> Endpoint | None:
    positional, keywords = _arguments(call)
    route = keywords.get("url", positional[0] if positional else None)
    if name == "stream":
        method = keywords.get("method")
        verb = _GET if method is None else _path(method, env, module)
    else:
        verb = _VERBS.get(name, _GET)
    path = None if route is None else _path(route, env, module)
    return None if verb is None or path is None else Endpoint(verb.upper(), path)


def _first_request(body: SgNode, receiver: str, env: Mapping[str, SgNode], module: _Module) -> _Request | None:
    """Return the first ``<receiver>.<verb>(…)`` call in ``body``, read or not, or None when there is none."""
    for call in body.find_all(kind="call"):
        name = _request_name(call, receiver)
        if name is not None:
            return _Request(_read_request(call, name, env, module), f"{receiver}.{name}")
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


def _delegated(body: SgNode, methods: Mapping[str, SgNode], module: _Module) -> _Request | None:
    """Return the request of the first call in ``body`` to a sibling method or module function that sends one."""
    for call in body.find_all(kind="call"):
        found = _leg(call, methods, module)
        leg_body = None if found is None else found[0].field("body")
        if found is None or leg_body is None:
            continue
        _, names, receiver = found
        positional, keywords = _arguments(call)
        env = dict(zip(names, positional, strict=False)) | {k: v for k, v in keywords.items() if k in names}
        request = _first_request(leg_body, receiver, env, module)
        callee = call.field("function")
        if request is not None and callee is not None:
            return _Request(request.endpoint, f"{request.call} (through {callee.text()})")
    return None


def _class_methods(cls: SgNode) -> dict[str, SgNode]:
    body = cls.field("body")
    methods: dict[str, SgNode] = {}
    for statement in [] if body is None else body.named_children():
        node = statement.field("definition") if statement.kind() == "decorated_definition" else statement
        if node is not None and node.kind() == "function_definition" and (name := node.field("name")) is not None:
            methods[name.text()] = node
    return methods


def _requests(client_module: Path) -> dict[str, _Request]:
    root = SgRoot(client_module.read_text(encoding="utf-8"), "python").root()
    module = _module(root)
    requests: dict[str, _Request] = {}
    for cls in root.find_all(kind="class_definition"):
        methods = _class_methods(cls)
        for name, method in methods.items():
            body = method.field("body")
            if name.startswith("_") or body is None:
                continue
            request = _first_request(body, "self", {}, module) or _delegated(body, methods, module)
            if request is not None:
                requests[name] = request
    return requests


def client_endpoints(client_module: Path) -> dict[str, Endpoint]:
    """Return the verb and path of each public method of each class in ``client_module``, read statically.

    A method's request is its first ``self.<verb>(path, …)`` call (``get``, ``post``, ``put``, ``patch``,
    ``delete``, ``head``; ``paginate`` is GET; ``stream`` is its literal ``method=``, GET by default). The path is a
    string or t-string literal, or a name bound to a module-level one; a t-string hole naming a module-level string
    is inlined, and any other hole becomes ``{expression}`` without its conversion or format spec. A method with no
    such call that delegates to a sibling method or a module-level function sending one is resolved one level: the
    leg's call is read with the leg's parameters bound to the caller's arguments. A method whose path is anything else
    (a parameter of the public method, a call, an f-string, a concatenation) is left out here and listed by
    ``unreadable_methods``; a method that sends no request, even two levels down, is in neither.
    """
    return {name: request.endpoint for name, request in _requests(client_module).items() if request.endpoint}


def unreadable_methods(client_module: Path) -> dict[str, str]:
    """Return each public method that sends a request whose path cannot be read, with the call that sends it.

    The call is ``self.get``, or ``self.get (through self._leg)`` for a one-level delegate.
    """
    return {name: request.call for name, request in _requests(client_module).items() if request.endpoint is None}


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


type _Key = tuple[str, tuple[str, ...]]
"""An endpoint as ``(VERB, normalised segments)``."""


@dataclass
class _Comparison:
    """What comparing the methods with the documented endpoints found."""

    problems: list[str]
    matched: dict[str, list[Endpoint]]


def _compare(methods: Mapping[str, Endpoint], snapshot: DocsSnapshot, file: str) -> _Comparison:
    found = _Comparison([], {})
    documented = [(endpoint, _segments(endpoint.path)) for endpoint in snapshot.endpoints]
    for name, endpoint in sorted(methods.items()):
        client = _segments(endpoint.path)
        candidates = [doc for doc, segs in documented if doc.verb == endpoint.verb and _matches(client, segs)]
        where = f"{name} calls {endpoint.verb} {endpoint.path}"
        if not candidates:
            found.problems.append(f"{where}, which is not in the snapshot {file}")
        elif len(candidates) > 1:
            listed = ", ".join(f"{doc.verb} {doc.path}" for doc in candidates)
            found.problems.append(f"{where}, which matches more than one documented path ({listed}); make it match one")
        found.matched[name] = candidates
    return found


def _key(endpoint: Endpoint) -> _Key:
    return (endpoint.verb, _segments(endpoint.path))


def _unknown_names(label: str, names: Collection[str], known: Collection[str]) -> list[str]:
    return [
        f"{label} names {name}, which is not a public method of the client that sends a request"
        for name in sorted(set(names) - set(known))
    ]


def _unreadable(unreadable: Mapping[str, str]) -> list[str]:
    return [
        f"{name} calls {call} with a path that is not a string, t-string or module-level constant (or a one-level "
        "delegate to one); spell the path as one of those so its name can be checked"
        for name, call in sorted(unreadable.items())
    ]


@dataclass(frozen=True)
class _Namer:
    """Derives the expected name of an endpoint: a ``"VERB path"`` override, else a name override, else the path's."""

    paths: frozenset[tuple[str, ...]]
    filler: frozenset[str]
    by_path: Mapping[_Key, str]
    by_name: Mapping[str, str]

    def derived(self, key: _Key) -> str:
        return _name(key[1], self.paths, self.filler)

    def expected(self, key: _Key) -> str:
        derived = self.derived(key)
        return self.by_path.get(key, self.by_name.get(derived, derived))


def _namer(universe: Collection[_Key], overrides: Mapping[str, str], filler: frozenset[str]) -> _Namer:
    by_path: dict[_Key, str] = {}
    by_name: dict[str, str] = {}
    for key, value in overrides.items():
        verb, space, path = key.partition(" ")
        if space:
            by_path[verb.upper(), _segments(path)] = value
        else:
            by_name[key] = value
    return _Namer(frozenset(segments for _, segments in universe), filler, by_path, by_name)


def _collisions(universe: Mapping[_Key, str], namer: _Namer) -> list[str]:
    """Report each pair of read paths that still derive one expected name, suggesting a ``"VERB path"`` key."""
    groups: dict[str, list[_Key]] = {}
    for key in sorted(universe, key=lambda key: (len(key[1]), universe[key], key[0])):
        groups.setdefault(namer.expected(key), []).append(key)
    return [
        f"{universe[first]} and {universe[other]} both name {name}; "
        f'add an override keyed "{other[0]} {universe[other]}"'
        for name, (first, *others) in groups.items()
        for other in others
    ]


def _stale(overrides: Mapping[str, str], known: Collection[_Key], namer: _Namer) -> list[str]:
    names = {namer.derived(key) for key in known}
    problems: list[str] = []
    for key, value in sorted(overrides.items()):
        verb, space, path = key.partition(" ")
        if (verb.upper(), _segments(path)) not in known if space else key not in names:
            problems.append(
                f"the override {key!r} -> {value!r} is stale: no endpoint is {'at' if space else 'named'} {key}"
            )
    return problems


def _missing_suffix(count: int) -> str:
    if count == 0:
        return ""
    return " (1 method has an unreadable path)" if count == 1 else f" ({count} methods have unreadable paths)"


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

    A read is a GET method or a method named in ``post_reads``. Its naming path is the documented path it matches
    when the snapshot has a source and it matches exactly one (R18), else its own path. Its name must be the
    ``overrides`` value keyed ``"VERB path"`` for that path (normalised per R16), else the value keyed by the derived
    name, else the derived name (R17): ``endpoint_name`` of the naming path, singularised when it is an item endpoint
    (its list's path plus one trailing ``{param}``) whose list shares the name. Also reported: a public method whose
    path cannot be read (unless in ``exempt_writes``); a documented GET with no method; a method whose endpoint the
    snapshot does not list, or lists more than once (both skipped when ``source`` is null); two read paths that still
    derive one name; a stale override key; a non-GET method in neither ``exempt_writes`` nor ``post_reads``; a name in
    ``exempt_writes`` or ``post_reads`` that is no method. Raise ``SnapshotError`` when the snapshot breaks its schema.
    """
    docs = load_snapshot(snapshot)
    filler = DEFAULT_FILLER if filler is None else filler
    requests = _requests(client_module)
    methods = {name: request.endpoint for name, request in requests.items() if request.endpoint is not None}
    unreadable = {
        name: request.call
        for name, request in requests.items()
        if request.endpoint is None and name not in exempt_writes
    }
    problems = _unreadable(unreadable)
    problems += [
        f"{name} sends {endpoint.verb} {endpoint.path}; list it in exempt_writes, or in post_reads if it reads"
        for name, endpoint in sorted(methods.items())
        if endpoint.verb != _GET and name not in exempt_writes and name not in post_reads
    ]
    problems += _unknown_names("exempt_writes", exempt_writes, requests)
    problems += _unknown_names("post_reads", post_reads, requests)
    reads = {name: endpoint for name, endpoint in methods.items() if endpoint.verb == _GET or name in post_reads}
    naming = dict(reads)
    if docs.source is None:
        universe = {_key(endpoint): endpoint.path.strip("/") for endpoint in reads.values()}
    else:
        found = _compare(methods, docs, snapshot.name)
        problems += found.problems
        matched = {doc for candidates in found.matched.values() for doc in candidates}
        problems += [
            f"the documented read {endpoint.verb} {endpoint.path} has no method{_missing_suffix(len(unreadable))}"
            for endpoint in docs.endpoints
            if endpoint.verb == _GET and endpoint not in matched
        ]
        documented_reads = [endpoint for endpoint in docs.endpoints if endpoint.verb == _GET] + [
            doc for name in post_reads for doc in found.matched.get(name, [])
        ]
        universe = {_key(endpoint): endpoint.path.strip("/") for endpoint in documented_reads}
        naming |= {name: found.matched[name][0] for name in reads if len(found.matched.get(name, [])) == 1}
    namer = _namer(universe, overrides, filler)
    for name, endpoint in sorted(reads.items()):
        expected = namer.expected(_key(naming[name]))
        if name != expected:
            problems.append(
                f"{name} reads {endpoint.verb} {endpoint.path} and should be named {expected} "
                "(or add an override with a reason)"
            )
    problems += _collisions(universe, namer)
    problems += _stale(overrides, {*universe, *map(_key, naming.values())}, namer)
    return problems
