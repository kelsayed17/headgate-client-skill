# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The method-name test helper: a client's ``test_method_names.py`` is ``assert check_names(...) == []``.

A read is named ``get_`` plus the literal segments of its path (``endpoint_name``), and every method is compared
with the docs snapshot saved beside the client as ``docs_paths.json`` (``headgate_verify.snapshot``).

The client is read statically (``headgate_verify.endpoints``). A client path is relative to the client's base URL, so
it matches a documented path when, after normalising both (strip ``/`` at either end, every ``{name}`` hole compares
as ``{}``, the verb upper-cased), it equals the documented path or is a suffix of it on a segment boundary (ruling
R16). A documented path equal to the client's wins over the suffix matches, so a client path ``/`` matches the
documented root, not every path. A method matching more than one documented path otherwise is a problem, never a
pick.

A public method that sends a request whose path is not a string, t-string or module-level constant (or a one-level
delegate to one) is reported by name, never dropped in silence, and a documented read with no method says how many
such methods there are. When the snapshot has a source and a method matches exactly one documented endpoint, its
expected name comes from the documented path, which carries any prefix the base URL holds; otherwise from the
client's own path (ruling R18). An ``overrides`` key is a derived name or ``"VERB path"`` (the path normalised as
above); a ``"VERB path"`` key wins over a name key, either is reported when stale, and two read paths that still
derive one name are reported with the ``"VERB path"`` key that would separate them (ruling R17).
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import inflect

from headgate_verify.config import Config, load_config
from headgate_verify.endpoints import GET, read_requests
from headgate_verify.snapshot import load_snapshot

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

    from headgate_verify.endpoints import Request
    from headgate_verify.snapshot import DocsSnapshot, Endpoint

DEFAULT_FILLER: frozenset[str] = Config().filler_words
"""The filler words dropped from a path when no other set is given: the verifier's default ``filler_words``."""

_VERSION = re.compile(r"^v\d+$|^vX$")
_HOLE = re.compile(r"\{[^{}]*\}")
_WORD_SPLIT = re.compile(r"[-_.]|(?<=[a-z0-9])(?=[A-Z])")
_INFLECT = inflect.engine()


def endpoint_name(path: str, *, filler: frozenset[str] = DEFAULT_FILLER, prefix: str = "get_") -> str:
    """Return the method name of a read of ``path``: ``prefix`` plus its literal words, joined by ``_``.

    Empty, ``{param}``, version (``v1``, ``vX``) and ``filler`` segments are dropped; a hole inside a segment is
    removed; each remaining segment splits on ``-``, ``_``, ``.`` and a lower-to-upper camelCase boundary (no split
    inside an all-caps run: ``CNMSshvol`` is one word); the words are lower-cased. A path with no word (``/``,
    ``/v1/``, ``/api/v1/{id}``) derives no name: raise ``ValueError`` (ruling R29); ``check_names`` asks for a
    ``"VERB path"`` override for such a read.
    """
    words = _words(path, filler)
    if not words:
        msg = f"the path {path!r} has no word to name it by; name it with a 'VERB path' override"
        raise ValueError(msg)
    return prefix + "_".join(words)


def _words(path: str, filler: frozenset[str]) -> list[str]:
    """Return the literal words of ``path`` that ``endpoint_name`` joins; empty when it has none."""
    words: list[str] = []
    for segment in path.split("/"):
        if not segment or _VERSION.match(segment) or segment in filler or _HOLE.fullmatch(segment):
            continue
        words.extend(word.lower() for word in _WORD_SPLIT.split(_HOLE.sub("", segment)) if word)
    return words


def _segments(path: str) -> tuple[str, ...]:
    stripped = _HOLE.sub("{}", path.strip("/"))
    return tuple(stripped.split("/")) if stripped else ()


def _matches(client: tuple[str, ...], documented: tuple[str, ...]) -> bool:
    return len(client) <= len(documented) and documented[len(documented) - len(client) :] == client


def _name(segments: tuple[str, ...], universe: Collection[tuple[str, ...]], filler: frozenset[str]) -> str | None:
    """Return the path's name, its last word singular when it is an item endpoint whose list shares the name.

    None when the path has no word (ruling R29). The singular is ``inflect``'s ``singular_noun`` of the last word, or
    the word itself when inflect finds it already singular (ruling R28).
    """
    words = _words("/".join(segments), filler)
    if not words:
        return None
    is_item = segments[-1] == "{}" and segments[:-1] in universe
    if is_item and _words("/".join(segments[:-1]), filler) == words:
        words[-1] = _INFLECT.singular_noun(words[-1]) or words[-1]
    return "get_" + "_".join(words)


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
        same_verb = [(doc, segs) for doc, segs in documented if doc.verb == endpoint.verb]
        exact = [doc for doc, segs in same_verb if segs == client]
        candidates = exact or [doc for doc, segs in same_verb if _matches(client, segs)]
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

    def derived(self, key: _Key) -> str | None:
        return _name(key[1], self.paths, self.filler)

    def expected(self, key: _Key) -> str | None:
        """Return the expected name; None when the path has no word and no ``"VERB path"`` override names it."""
        if key in self.by_path:
            return self.by_path[key]
        derived = self.derived(key)
        return None if derived is None else self.by_name.get(derived, derived)


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
        expected = namer.expected(key)
        if expected is not None:
            groups.setdefault(expected, []).append(key)
    return [
        f"{universe[first]} and {universe[other]} both name {name}; "
        f'add an override keyed "{other[0]} {universe[other]}"'
        for name, (first, *others) in groups.items()
        for other in others
    ]


def _stale(overrides: Mapping[str, str], known: Collection[_Key], namer: _Namer) -> list[str]:
    names = {name for key in known if (name := namer.derived(key)) is not None}
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


@dataclass(frozen=True)
class _Methods:
    """The client's public methods that send a request, sorted by what the name check does with each."""

    sent: Mapping[str, Endpoint]
    """Every method whose request reads, with its endpoint."""
    unreadable: Mapping[str, str]
    """Every method whose path cannot be read and is not an exempt write, with the call that sends it."""
    reads: Mapping[str, Endpoint]
    """The methods of ``sent`` that read: a GET, or a method named in ``post_reads``."""


def _sort_methods(
    requests: Mapping[str, Request], exempt_writes: Collection[str], post_reads: Collection[str]
) -> tuple[_Methods, list[str]]:
    """Sort the client's requests, and report unreadable paths, unlisted writes and unknown listed names."""
    sent = {name: request.endpoint for name, request in requests.items() if request.endpoint is not None}
    unreadable = {
        name: request.call
        for name, request in requests.items()
        if request.endpoint is None and name not in exempt_writes
    }
    problems = _unreadable(unreadable)
    problems += [
        f"{name} sends {endpoint.verb} {endpoint.path}; list it in exempt_writes, or in post_reads if it reads"
        for name, endpoint in sorted(sent.items())
        if endpoint.verb != GET and name not in exempt_writes and name not in post_reads
    ]
    problems += _unknown_names("exempt_writes", exempt_writes, requests)
    problems += _unknown_names("post_reads", post_reads, requests)
    reads = {name: endpoint for name, endpoint in sent.items() if endpoint.verb == GET or name in post_reads}
    return _Methods(sent, unreadable, reads), problems


@dataclass(frozen=True)
class _Universe:
    """The read paths names are derived from, and the endpoint each of the client's reads is named after."""

    paths: Mapping[_Key, str]
    """Each read endpoint, keyed as ``(VERB, segments)``, with its path stripped of ``/`` at either end."""
    naming: Mapping[str, Endpoint]
    """Each read method's naming endpoint: the documented one it alone matches (R18), else its own."""


def _universe(
    methods: _Methods, docs: DocsSnapshot, file: str, post_reads: Collection[str]
) -> tuple[_Universe, list[str]]:
    """Return the read universe, and report what comparing the methods with the snapshot finds.

    With no ``source`` the client's own reads are the universe and nothing is compared.
    """
    if docs.source is None:
        paths = {_key(endpoint): endpoint.path.strip("/") for endpoint in methods.reads.values()}
        return _Universe(paths, dict(methods.reads)), []
    found = _compare(methods.sent, docs, file)
    matched = {doc for candidates in found.matched.values() for doc in candidates}
    problems = found.problems + [
        f"the documented read {endpoint.verb} {endpoint.path} has no method{_missing_suffix(len(methods.unreadable))}"
        for endpoint in docs.endpoints
        if endpoint.verb == GET and endpoint not in matched
    ]
    documented_reads = [endpoint for endpoint in docs.endpoints if endpoint.verb == GET] + [
        doc for name in post_reads for doc in found.matched.get(name, [])
    ]
    paths = {_key(endpoint): endpoint.path.strip("/") for endpoint in documented_reads}
    naming = dict(methods.reads) | {
        name: found.matched[name][0] for name in methods.reads if len(found.matched.get(name, [])) == 1
    }
    return _Universe(paths, naming), problems


def _misnamed(reads: Mapping[str, Endpoint], universe: _Universe, namer: _Namer) -> list[str]:
    """Report each read whose name is not the expected one, then each read path that derives no name (R29)."""
    problems: list[str] = []
    nameless = {key: "/" + path for key, path in universe.paths.items() if namer.expected(key) is None}
    for name, endpoint in sorted(reads.items()):
        naming = universe.naming[name]
        key = _key(naming)
        expected = namer.expected(key)
        if expected is None:
            nameless.setdefault(key, "/" + naming.path.strip("/"))
        elif name != expected:
            problems.append(
                f"{name} reads {endpoint.verb} {endpoint.path} and should be named {expected} "
                "(or add an override with a reason)"
            )
    problems += [
        f'the read {verb} {path} derives no name from its path; add an override keyed "{verb} {path}"'
        for (verb, _), path in sorted(nameless.items())
    ]
    return problems


def check_names(  # noqa: PLR0913 -- the documented signature: two files and four keyword-only knobs
    client_module: Path,
    snapshot: Path,
    *,
    overrides: Mapping[str, str] = {},
    exempt_writes: Collection[str] = (),
    post_reads: Collection[str] | None = None,
    filler: frozenset[str] | None = None,
) -> list[str]:
    """Return one sentence per naming problem of ``client_module`` against the ``snapshot`` file; ``[]`` is clean.

    A read is a GET method or a method named in ``post_reads``. Its naming path is the documented path it matches
    when the snapshot has a source and it matches exactly one (R18), else its own path. Its name must be the
    ``overrides`` value keyed ``"VERB path"`` for that path (normalised per R16), else the value keyed by the derived
    name, else the derived name (R17): ``endpoint_name`` of the naming path, singularised when it is an item endpoint
    (its list's path plus one trailing ``{param}``) whose list shares the name. A read whose path has no word is
    reported as needing a ``"VERB path"`` override unless one names it (R29). Also reported: a public method whose
    path cannot be read (unless in ``exempt_writes``); a documented GET with no method; a method whose endpoint the
    snapshot does not list, or lists more than once (both skipped when ``source`` is null); two read paths that still
    derive one name; a stale override key; a non-GET method in neither ``exempt_writes`` nor ``post_reads``; a name in
    ``exempt_writes`` or ``post_reads`` that is no method. Raise ``SnapshotError`` when the snapshot breaks its schema.

    ``filler`` and ``post_reads`` left out (None) are read from ``[tool.headgate-verify]`` in the ``pyproject.toml``
    nearest ``client_module`` (``filler-words``, ``post-reads``), or are the verifier's defaults when it has no such
    table (ruling R26); a value passed in wins. Raise ``ConfigError`` when that table is malformed.
    """
    docs = load_snapshot(snapshot)
    if filler is None or post_reads is None:
        project = load_config(client_module)
        filler = project.filler_words if filler is None else filler
        post_reads = project.post_reads if post_reads is None else post_reads
    methods, problems = _sort_methods(read_requests(client_module), exempt_writes, post_reads)
    universe, compared = _universe(methods, docs, snapshot.name, post_reads)
    problems += compared
    namer = _namer(universe.paths, overrides, filler)
    problems += _misnamed(methods.reads, universe, namer)
    problems += _collisions(universe.paths, namer)
    problems += _stale(overrides, {*universe.paths, *map(_key, universe.naming.values())}, namer)
    return problems
