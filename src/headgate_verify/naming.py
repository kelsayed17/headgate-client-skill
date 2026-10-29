# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The method-name test helper: a client's ``test_method_names.py`` is ``assert check_names(...) == []``.

A method is named from the vendor's spec where the docs snapshot (``docs_paths.json``, ``headgate_verify.snapshot``)
carries an ``operationId`` that passes the gate (``spec_name``), and a read is otherwise named ``get_`` plus the
literal segments of its path (``endpoint_name``). Every method is compared with the snapshot. What neither rule names
well is listed by ``review_names`` for a person or an agent to judge; the check itself stays deterministic and offline.

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
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import inflect

from headgate_verify.config import Config, load_config
from headgate_verify.endpoints import GET, read_requests
from headgate_verify.snapshot import load_snapshot

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence
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


# Names from the vendor's spec.
#
# No word list is kept. A word the endpoint itself states (a word of its path, of the client's return models' names,
# of the spec's schema names) is a noun; the first word of the operationId it does not state is the id's verb. So
# ``listClients`` reads as ``list`` + ``clients``, ``postOrder`` takes the summary's verb ("Create an Order"), and a
# word the vendor adds that the endpoint never states (``Single``, ``Open``) is dropped unless dropping it collides.

_ID_VERSION = re.compile(r"(?i)(?<![a-z])v(?:\d+|x)(?=[A-Z_\-]|$)|(?<=[a-z])V(?:\d+|X)(?=[A-Z_\-]|$)")
_ACRONYM_PLURAL = re.compile(r"([A-Z]{2,})s(?=[A-Z0-9_\W]|$)")
_ID_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_NOT_WORD = re.compile(r"[^a-z0-9]+")
_MODEL = re.compile(r"[A-Z][A-Za-z0-9]+")
_WHOLE_HOLE = re.compile(r"/\{(\w+)[^{}]*\}(?=/|$)")
_FASTAPI_ID = re.compile(r"_(?:get|post|put|patch|delete|head)$")
_FASTAPI_UNDERSCORES = 4
"""FastAPI's default id ``<function>_<path…>_<verb>`` has at least this many underscores."""
_PATH_VERSION = re.compile(r"_v\d+_")
_NAMESPACE_SHARE = 0.8
"""A leading word this share of a spec's ids carry, heading more than one HTTP verb, is the spec's namespace."""
_NAMESPACE_MIN_IDS = 5
_NAMESPACE_MIN_VERBS = 2
_EXTENSION = re.compile(r"\.[A-Za-z0-9]+$")
_MIN_COMPARABLE = 2
"""inflect compares words of two letters or more (``dm`` and ``dms``); a single letter compares only by spelling."""
_MIN_GLUED_PIECE = 4
"""A piece of a glued path word (``government`` in ``governmententities``) has four letters or more."""
_SINGULAR_PLURAL = frozenset({"s:p", "p:s"})


def id_words(text: str) -> list[str]:
    """Return the lower-case words of an operationId, summary or schema name; an acronym's plural is one word.

    ``listClients`` is ``list clients``, ``getIPOsCalendar`` is ``get ipos calendar``, ``HTTPServer`` is
    ``http server``, and ``Create an Order`` is ``create an order``.
    """
    text = _ACRONYM_PLURAL.sub(lambda found: found.group(1) + "S", text)
    return [word for word in _NOT_WORD.split(_ID_CAMEL.sub("_", text).lower()) if word]


def _path_words(path: str) -> list[str]:
    """Return every literal word of ``path``: holes and a file extension removed, no filler or version rule."""
    return [word for segment in path.split("/") for word in id_words(_EXTENSION.sub("", _HOLE.sub("", segment)))]


def spec_namespace(endpoints: Collection[Endpoint]) -> tuple[str, ...]:
    """Return the leading words that name a spec rather than its operations, or ``()`` when there are none.

    They are the longest run of leading words that at least 80% of each HTTP verb's ids share, in a spec of five or
    more ids over more than one verb (coinbase's ``RetailBrokerageApi_``). A shared verb word such as ``get`` heads
    only the reads, so it is never taken for a namespace.
    """
    named = [endpoint for endpoint in endpoints if endpoint.operation_id]
    by_verb: dict[str, list[list[str]]] = {}
    for endpoint in named:
        by_verb.setdefault(endpoint.verb, []).append(id_words(endpoint.operation_id.rsplit(".", 1)[-1]))
    if len(named) < _NAMESPACE_MIN_IDS or len(by_verb) < _NAMESPACE_MIN_VERBS:
        return ()
    namespace: tuple[str, ...] = ()
    while True:
        size = len(namespace) + 1
        candidate = Counter(tuple(words[:size]) for ids in by_verb.values() for words in ids).most_common(1)[0][0]
        shared = all(
            sum(tuple(words[:size]) == candidate for words in ids) >= _NAMESPACE_SHARE * len(ids)
            for ids in by_verb.values()
        )
        if len(candidate) < size or not shared:
            return namespace
        namespace = candidate


def _strip(words: list[str], namespace: Sequence[str]) -> list[str]:
    return words[len(namespace) :] if namespace and words[: len(namespace)] == list(namespace) else words


@dataclass(frozen=True)
class _Stated:
    """The words an endpoint states: its path's literal words, its client's model names, its spec's schema names.

    The path and the models are what the endpoint itself says, and find the id's verb; the schema names also count
    for keeping a noun, but a generated schema name often repeats the id's verb (``CreateOrderRequest``).
    """

    path: tuple[str, ...]
    models: tuple[str, ...]
    schemas: tuple[str, ...]

    def says(self, word: str) -> bool:
        """Whether the path or a model states ``word``: equal up to number, or a piece of a glued path word."""
        return _among(word, (*self.path, *self.models)) or (
            len(word) >= _MIN_GLUED_PIECE and any(len(other) > len(word) + 2 and word in other for other in self.path)
        )

    def keeps(self, word: str) -> bool:
        """Whether a noun ``word`` stays in the name: the endpoint states it, or a schema name does."""
        return self.says(word) or _among(word, self.schemas)


def _among(word: str, others: Sequence[str]) -> bool:
    return any(
        word == other or (min(len(word), len(other)) >= _MIN_COMPARABLE and _INFLECT.compare(word, other) is not False)
        for other in others
    )


def _stated(endpoint: Endpoint, models: Collection[str]) -> _Stated:
    def words(names: Collection[str]) -> tuple[str, ...]:
        return tuple(word for name in names for word in id_words(name.rsplit(".", 1)[-1]))

    schemas = words((endpoint.response_schema, endpoint.request_schema))
    return _Stated(tuple(_path_words(endpoint.path)), words(models), schemas)


def _rejected(operation_id: str, words: list[str], path: str, stated: _Stated) -> str:
    """Return why the id cannot name a method (the gate), or ``""`` when it can."""
    if "." in operation_id:
        return "it is a code path (it holds a '.')"
    fastapi = _FASTAPI_ID.search(operation_id) is not None and operation_id.count("_") >= _FASTAPI_UNDERSCORES
    if fastapi or ("-" in operation_id and "_" in operation_id) or _PATH_VERSION.search(operation_id) is not None:
        return "it is the path written out"
    for hole_name in _WHOLE_HOLE.findall(path):
        hole = id_words(hole_name)
        if len(hole) == 1 and hole != ["id"]:
            continue
        for at in range(len(words) - len(hole) + 1):
            if words[at : at + len(hole)] == hole and (at == 0 or stated.says(words[at - 1])):
                return f"it spells the path hole {{{hole_name}}} as words"
    return ""


def _number(word: str, endpoint: Endpoint) -> str:
    """Give a read's last noun its path's number when the path ends in a comparable word, else an array's plural."""
    if not word.isalpha() or len(word) < _MIN_COMPARABLE:
        return word
    literals = _path_words(endpoint.path)
    if literals and not _HOLE.search(endpoint.path.rstrip("/").rsplit("/", 1)[-1]):
        last = literals[-1]
        if len(last) >= _MIN_COMPARABLE and _INFLECT.compare(word, last) in _SINGULAR_PLURAL:
            return last
        if last == word:
            return word
    if endpoint.response_shape == "array" and not _INFLECT.singular_noun(word):
        return str(_INFLECT.plural_noun(word))
    return word


def _once(words: Sequence[str], stated: _Stated) -> list[str]:
    """Drop a stated word's repeats; an unstated link word (``by``) may recur."""
    return [word for index, word in enumerate(words) if word not in words[:index] or not stated.keeps(word)]


def _action(words: Sequence[str], path: str) -> str | None:
    """Return the id's first word that the path's last segment holds, when that segment is literal: its action.

    An id whose every word the endpoint states names its verb in the path: ``leaveCall`` on ``/calls/{id}/leave``,
    ``CancelOrders`` on ``/orders/batch_cancel``.
    """
    last = path.rstrip("/").rsplit("/", 1)[-1]
    if _HOLE.search(last):
        return None
    action = id_words(_EXTENSION.sub("", last))
    return next((word for word in words if word in action), None)


@dataclass(frozen=True)
class SpecName:
    """The name an operation's spec gives a method, or why it gives none.

    ``name`` keeps only the words the endpoint states; ``full`` keeps every word of the id, which a ``name`` that
    collides falls back to; ``rejected`` says why the id is not used, and is ``""`` when ``name`` is set.
    """

    name: str = ""
    full: str = ""
    rejected: str = ""


def spec_name(
    endpoint: Endpoint,
    *,
    prefix: str = "get",
    write: bool = False,
    models: Collection[str] = (),
    namespace: Sequence[str] = (),
) -> SpecName:
    """Return the name ``endpoint``'s ``operation_id`` gives its method, or why it gives none.

    ``endpoint`` is a documented endpoint carrying its spec's details. A read's name is ``prefix`` (the call shape:
    ``get``, or a caller's ``walk``, ``fetch``, ``stream``) and the id's nouns, the id's own verb dropped; a write's
    is the id's verb and nouns, the verb from the summary when the id's only repeats the HTTP verb (``postOrder``,
    "Create an Order"). ``models`` are the client's return model names, which the endpoint states as well as its path
    and schemas; ``namespace`` is the spec's (``spec_namespace``), stripped from the id and the summary.
    """
    if not endpoint.operation_id:
        return SpecName(rejected="the spec gives it no operationId")
    words = _strip(id_words(_ID_VERSION.sub("", endpoint.operation_id.rsplit(".", 1)[-1])), namespace)
    stated = _stated(endpoint, models)
    if rejected := _rejected(endpoint.operation_id, words, endpoint.path, stated):
        return SpecName(rejected=f"the operationId {endpoint.operation_id!r} is not used: {rejected}")
    verb_at = next((index for index, word in enumerate(words) if not stated.says(word)), None)
    nouns = words if verb_at is None else words[:verb_at] + words[verb_at + 1 :]
    kept = [word for word in nouns if stated.keeps(word)]
    if not kept:
        return SpecName(rejected=f"the operationId {endpoint.operation_id!r} states no word of the endpoint")
    if not write:
        kept[-1] = _number(kept[-1], endpoint)
        return SpecName("_".join(_once([prefix, *kept], stated)), "_".join(_once([prefix, *nouns], stated)))
    verb = None if verb_at is None else words[verb_at]
    if verb is None or verb == endpoint.verb.lower():
        summary = _strip(id_words(endpoint.summary), namespace)
        if summary and not stated.says(summary[0]):
            verb = summary[0]
    if verb is None:
        verb = _action(words, endpoint.path)
        nouns = [word for word in words if word != verb]
        kept = [word for word in nouns if stated.keeps(word)]
    if verb is None or not kept:
        return SpecName(rejected=f"the operationId {endpoint.operation_id!r} and its summary name no verb")
    return SpecName("_".join(_once([verb, *kept], stated)), "_".join(_once([verb, *nouns], stated)))


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
    """Derives an endpoint's expected name: a ``"VERB path"`` override, else a name override, else its derived name.

    The derived name is the spec's (``spec``), else the path's for a read; a write the spec does not name has none.
    """

    paths: frozenset[tuple[str, ...]]
    filler: frozenset[str]
    by_path: Mapping[_Key, str]
    by_name: Mapping[str, str]
    spec: Mapping[_Key, str]
    writes: frozenset[_Key]

    def path_name(self, key: _Key) -> str | None:
        return None if key in self.writes else _name(key[1], self.paths, self.filler)

    def derived(self, key: _Key) -> str | None:
        return self.spec.get(key) or self.path_name(key)

    def expected(self, key: _Key) -> str | None:
        """Return the expected name; None when nothing derives one and no ``"VERB path"`` override names it."""
        if key in self.by_path:
            return self.by_path[key]
        derived = self.derived(key)
        return None if derived is None else self.by_name.get(derived, derived)

    def overridden(self, key: _Key) -> bool:
        return key in self.by_path or self.derived(key) in self.by_name


def _overrides(overrides: Mapping[str, str]) -> tuple[dict[_Key, str], dict[str, str]]:
    """Split the overrides into ``"VERB path"`` keys and name keys."""
    by_path: dict[_Key, str] = {}
    by_name: dict[str, str] = {}
    for key, value in overrides.items():
        verb, space, path = key.partition(" ")
        if space:
            by_path[verb.upper(), _segments(path)] = value
        else:
            by_name[key] = value
    return by_path, by_name


@dataclass(frozen=True)
class _Entry:
    """A documented endpoint the spec may name: its details, the client's model names for it, and whether it writes."""

    documented: Endpoint
    models: tuple[str, ...]
    write: bool


@dataclass(frozen=True)
class _SpecNames:
    """The spec's name of each endpoint that keeps one, and why each endpoint with an operationId keeps none."""

    names: Mapping[_Key, str]
    notes: Mapping[_Key, str]


def _spec_names(entries: Mapping[_Key, _Entry], path_names: Mapping[_Key, str | None]) -> _SpecNames:
    """Name each entry from its spec; a name that collides keeps every id word, and one that still does is dropped.

    A collision is with any other endpoint's name, the spec's or the path's.
    """
    namespace = spec_namespace([entry.documented for entry in entries.values()])
    given = {
        key: spec_name(entry.documented, write=entry.write, models=entry.models, namespace=namespace)
        for key, entry in entries.items()
    }
    chosen = {key: result.name for key, result in given.items() if result.name}

    def clashing() -> list[_Key]:
        others = [name for key, name in path_names.items() if key not in chosen and name is not None]
        counts = Counter([*chosen.values(), *others])
        return [key for key, name in chosen.items() if counts[name] > 1]

    for key in clashing():
        chosen[key] = given[key].full
    notes = {
        key: result.rejected
        for key, result in given.items()
        if result.rejected and entries[key].documented.operation_id
    }
    for key in clashing():
        notes[key] = f"its spec name {chosen.pop(key)} is another endpoint's too"
    return _SpecNames(chosen, notes)


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
    """Every method whose path cannot be read, with the call that sends it."""
    exempt: frozenset[str]
    """The methods listed in ``exempt_writes``."""
    reads: Mapping[str, Endpoint]
    """The methods of ``sent`` that read: a GET, or a method named in ``post_reads``."""
    models: Mapping[str, tuple[str, ...]]
    """Each method's return model names: the capitalised names in its return annotation."""


def _sort_methods(
    requests: Mapping[str, Request], exempt_writes: Collection[str], post_reads: Collection[str]
) -> tuple[_Methods, list[str]]:
    """Sort the client's requests, and report unreadable paths, unlisted writes and unknown listed names."""
    sent = {name: request.endpoint for name, request in requests.items() if request.endpoint is not None}
    unreadable = {name: request.call for name, request in requests.items() if request.endpoint is None}
    problems = _unreadable({name: call for name, call in unreadable.items() if name not in exempt_writes})
    problems += [
        f"{name} sends {endpoint.verb} {endpoint.path}; list it in exempt_writes, or in post_reads if it reads"
        for name, endpoint in sorted(sent.items())
        if endpoint.verb != GET and name not in exempt_writes and name not in post_reads
    ]
    problems += _unknown_names("exempt_writes", exempt_writes, requests)
    problems += _unknown_names("post_reads", post_reads, requests)
    reads = {name: endpoint for name, endpoint in sent.items() if endpoint.verb == GET or name in post_reads}
    models = {name: tuple(_MODEL.findall(request.returns)) for name, request in requests.items()}
    return _Methods(sent, unreadable, frozenset(exempt_writes), reads, models), problems


@dataclass(frozen=True)
class _Universe:
    """The read paths names are derived from, and the endpoint each of the client's methods is named after."""

    paths: Mapping[_Key, str]
    """Each read endpoint, keyed as ``(VERB, segments)``, with its path stripped of ``/`` at either end."""
    naming: Mapping[str, Endpoint]
    """Each read method's naming endpoint: the documented one it alone matches (R18), else its own."""
    writes: Mapping[str, Endpoint]
    """Each write method's documented endpoint, when it matches exactly one."""
    documented: Mapping[_Key, Endpoint]
    """Each documented endpoint the methods are named after, with its spec details; empty with no ``source``."""


def _universe(
    methods: _Methods, docs: DocsSnapshot, file: str, post_reads: Collection[str]
) -> tuple[_Universe, list[str]]:
    """Return the read universe, and report what comparing the methods with the snapshot finds.

    With no ``source`` the client's own reads are the universe and nothing is compared.
    """
    if docs.source is None:
        paths = {_key(endpoint): endpoint.path.strip("/") for endpoint in methods.reads.values()}
        return _Universe(paths, dict(methods.reads), {}, {}), []
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
    single = {name: candidates[0] for name, candidates in found.matched.items() if len(candidates) == 1}
    naming = dict(methods.reads) | {name: doc for name, doc in single.items() if name in methods.reads}
    writes = {name: doc for name, doc in single.items() if name not in methods.reads}
    documented = {_key(doc): doc for doc in [*documented_reads, *writes.values()]}
    return _Universe(paths, naming, writes, documented), problems


def _namer(
    universe: _Universe, methods: _Methods, overrides: Mapping[str, str], filler: frozenset[str]
) -> tuple[_Namer, _SpecNames]:
    """Return the namer of the universe's endpoints, with the spec's names, and the spec names' notes."""
    by_path, by_name = _overrides(overrides)
    writes = frozenset(_key(doc) for doc in universe.writes.values()) - set(universe.paths)
    plain = _Namer(frozenset(segments for _, segments in universe.paths), filler, by_path, by_name, {}, writes)
    models: dict[_Key, set[str]] = {}
    for name, endpoint in [*universe.naming.items(), *universe.writes.items()]:
        models.setdefault(_key(endpoint), set()).update(methods.models.get(name, ()))
    entries = {
        key: _Entry(doc, tuple(sorted(models.get(key, ()))), key in writes) for key, doc in universe.documented.items()
    }
    spec = _spec_names(entries, {key: plain.path_name(key) for key in universe.paths})
    return _Namer(plain.paths, filler, by_path, by_name, spec.names, writes), spec


def _origin(key: _Key, namer: _Namer, documented: Mapping[_Key, Endpoint]) -> str:
    if key in namer.spec and not namer.overridden(key):
        return f" (from the spec's operationId {documented[key].operation_id!r})"
    return ""


def _misnamed(methods: _Methods, universe: _Universe, namer: _Namer) -> list[str]:
    """Report each method whose name is not the expected one, then each read path that derives no name (R29)."""
    problems: list[str] = []
    nameless = {key: "/" + path for key, path in universe.paths.items() if namer.expected(key) is None}
    named = [(name, methods.reads[name], universe.naming[name]) for name in methods.reads]
    named += [(name, methods.sent[name], doc) for name, doc in universe.writes.items()]
    for name, endpoint, naming in sorted(named, key=lambda item: item[0]):
        key = _key(naming)
        expected = namer.expected(key)
        if expected is None:
            if key not in namer.writes:
                nameless.setdefault(key, "/" + naming.path.strip("/"))
        elif name != expected:
            problems.append(
                f"{name} {'reads' if key not in namer.writes else 'sends'} {endpoint.verb} {endpoint.path} and "
                f"should be named {expected}{_origin(key, namer, universe.documented)} "
                "(or add an override with a reason)"
            )
    problems += [
        f'the read {verb} {path} derives no name from its path; add an override keyed "{verb} {path}"'
        for (verb, _), path in sorted(nameless.items())
    ]
    return problems


def _review(methods: _Methods, universe: _Universe, namer: _Namer, spec: _SpecNames) -> list[str]:
    """List the names the rules cannot produce well, for a person or an agent to judge against the docs."""
    review: list[str] = []
    by_key: dict[_Key, list[str]] = {}
    paths: dict[_Key, str] = {}
    for name, naming in [*universe.naming.items(), *universe.writes.items()]:
        by_key.setdefault(_key(naming), []).append(name)
        paths[_key(naming)] = "/" + naming.path.strip("/")
    for key, names in sorted(by_key.items(), key=lambda item: min(item[1])):
        verb, where = key[0], paths[key]
        override = f'an override keyed "{verb} {where}" with a reason'
        first = min(names)
        if len(names) > 1:
            listed = " and ".join(sorted(names))
            review.append(
                f"{listed} all send {verb} {where}; one path names one method, so check each against the docs"
            )
        if namer.overridden(key):
            continue
        if key in spec.notes and key in namer.writes:
            review.append(f"{first} sends {verb} {where}, which no rule names: {spec.notes[key]}; check its name")
        elif namer.expected(key) is None and key not in namer.writes:
            review.append(
                f"{first} reads {verb} {where}, whose path has no word; name it from the docs with {override}"
            )
        elif key in spec.notes:
            review.append(
                f"{first} reads {verb} {where} by its path's name {namer.path_name(key)}: {spec.notes[key]}; if that "
                f"name does not say what the endpoint does, name it from the docs with {override}"
            )
    review += [
        f"{name} calls {call} with a path that cannot be read, so its name is unchecked; check it against the docs"
        for name, call in sorted(methods.unreadable.items())
    ]
    return review


@dataclass(frozen=True)
class _Knobs:
    """``check_names``' keyword arguments."""

    overrides: Mapping[str, str]
    exempt_writes: Collection[str]
    post_reads: Collection[str] | None
    filler: frozenset[str] | None


@dataclass(frozen=True)
class _Analysis:
    problems: list[str]
    review: list[str]


def _analyse(client_module: Path, snapshot: Path, knobs: _Knobs) -> _Analysis:
    docs = load_snapshot(snapshot)
    filler, post_reads = knobs.filler, knobs.post_reads
    if filler is None or post_reads is None:
        project = load_config(client_module)
        filler = project.filler_words if filler is None else filler
        post_reads = project.post_reads if post_reads is None else post_reads
    methods, problems = _sort_methods(read_requests(client_module), knobs.exempt_writes, post_reads)
    universe, compared = _universe(methods, docs, snapshot.name, post_reads)
    problems += compared
    namer, spec = _namer(universe, methods, knobs.overrides, filler)
    problems += _misnamed(methods, universe, namer)
    problems += _collisions(universe.paths, namer)
    known = {*universe.paths, *map(_key, universe.naming.values()), *namer.writes}
    problems += _stale(knobs.overrides, known, namer)
    return _Analysis(problems, _review(methods, universe, namer, spec))


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
    name, else the derived name (R17). The derived name is the spec's when the snapshot carries the endpoint's
    ``operation_id`` and ``spec_name`` gives one that no other endpoint's name takes (a colliding name keeps every id
    word, and one that still collides is dropped); else ``endpoint_name`` of the naming path, singularised when it is
    an item endpoint (its list's path plus one trailing ``{param}``) whose list shares the name. A write (in
    ``exempt_writes``) matching exactly one documented endpoint is held to the spec's name the same way, and is
    unchecked when the spec gives none. A read whose path has no word is reported as needing a ``"VERB path"``
    override unless one names it (R29). Also reported: a public method whose path cannot be read (unless in
    ``exempt_writes``); a documented GET with no method; a method whose endpoint the snapshot does not list, or lists
    more than once (both skipped when ``source`` is null); two read paths that still derive one name; a stale override
    key; a non-GET method in neither ``exempt_writes`` nor ``post_reads``; a name in ``exempt_writes`` or
    ``post_reads`` that is no method. Raise ``SnapshotError`` when the snapshot breaks its schema.

    ``filler`` and ``post_reads`` left out (None) are read from ``[tool.headgate-verify]`` in the ``pyproject.toml``
    nearest ``client_module`` (``filler-words``, ``post-reads``), or are the verifier's defaults when it has no such
    table (ruling R26); a value passed in wins. Raise ``ConfigError`` when that table is malformed.
    """
    return _analyse(client_module, snapshot, _Knobs(overrides, exempt_writes, post_reads, filler)).problems


def review_names(  # noqa: PLR0913 -- check_names' signature: two files and four keyword-only knobs
    client_module: Path,
    snapshot: Path,
    *,
    overrides: Mapping[str, str] = {},
    exempt_writes: Collection[str] = (),
    post_reads: Collection[str] | None = None,
    filler: frozenset[str] | None = None,
) -> list[str]:
    """Return one sentence per name the rules cannot produce well, for a person or an agent to judge; never a failure.

    Takes ``check_names``' arguments. Listed: a method named by its path because the spec's ``operationId`` was
    rejected, states no word of the endpoint, or collided (the sentence says which); a write the spec does not name; a
    read whose path has no word; two methods on one endpoint; a method whose path cannot be read. An endpoint an
    override already names is not listed. The checker stays deterministic: judging whether a path's name reads well,
    and proposing a better one, is the reviewer's, recorded as an override with a reason.
    """
    return _analyse(client_module, snapshot, _Knobs(overrides, exempt_writes, post_reads, filler)).review
