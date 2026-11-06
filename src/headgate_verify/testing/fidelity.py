# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Wire fidelity for a client's msgspec structs: undeclared wire keys, unexercised fields, and the recorded debt.

Statement coverage says little about a client: ``models.py`` is field *declarations* run at import, so it is covered
for free, and a client method is a flat one-liner. What it cannot see is a key the provider sends that no struct
declares, which msgspec drops at decode without a word. :func:`undeclared_keys` walks a recorded body against the
target the client decodes it into and names each such key; :func:`unexercised_fields` names each declared field no
recorded body fills, which is a field no test proves parses.

The check is held **test-side** on purpose. ``forbid_unknown_fields=True`` on the structs would enforce the same thing
at decode time, and make the live request path raise the day a provider adds a field: a production outage traded for
a gap a test can report.

Walk at the decode boundary
---------------------------
Pass each body with the target the client actually decodes it into (``decoder(Envelope)``'s argument), not the
method's return annotation: a method that unwraps ``results`` returns ``list[Row]``, and walking the whole envelope
against ``Row`` reports the envelope's own keys on every body.

Positional wires: ``array_like=True``
-------------------------------------
A struct with ``array_like=True`` reads a row sent as a JSON array. msgspec silently TRUNCATES an over-long row there
(``[1, 2, 3]`` into a two-field struct decodes as ``(1, 2)``), which is exactly the drift this module exists to catch,
so the walk reads such a row by position: position *i* is the *i*-th field, and a position past the last field is
reported as ``Struct.[i]``. :func:`unexercised_fields` counts a non-null position as populating its field. A list
arriving where an ``array_like`` struct is declared is always read as ONE row, so a bare top-level array of positional
rows is passed as ``list[Row]``. Names are not checked (a positional row has none).

The recorded debt
-----------------
What a package's structs knowingly leave out, in either direction, is recorded in ``_fidelity_baseline.toml`` beside
its tests (:func:`load_baseline`) and compared for EXACT equality with what its bodies show
(:func:`assert_matches_baseline`): a new finding fails as drift, and an entry nothing shows any more fails as stale, so
the record cannot rot in either direction. A package's fidelity test is three lines::

    found = findings((json.loads(body), endpoint.envelope) for endpoint in MANIFEST for body in bodies(endpoint))
    assert_matches_baseline(found, load_baseline(Path(__file__).parent))
"""

import re
import tomllib
import types
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple, get_args, get_origin

import msgspec
import msgspec.structs

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

# One case, not two: since 3.14 ``typing.Union is types.UnionType``, so both
# spellings of a union share an origin. Kept as a tuple because the membership
# test reads the same either way and does not depend on that identity holding.
_UNION_ORIGINS = (types.UnionType, typing.Union)

_ByWire = dict[str, msgspec.structs.FieldInfo]
# Called at every struct node the walk reaches, with that node's mapping and its
# wire-name index. The two directions differ only in what they record here.
_Visitor = Callable[[type[msgspec.Struct], Mapping[str, Any], _ByWire], None]


@cache
def _by_wire(struct: type[msgspec.Struct]) -> _ByWire:
    """Wire-name index for *struct*, cached on the type.

    ``msgspec.structs.fields`` is a pure function of an immutable class object — a
    Struct's fields are fixed at class creation and cannot change at runtime — so caching
    on the type carries no staleness risk. That is stated rather than left implicit,
    because it is the whole reason this is safe.

    It matters because the walk asks per NODE, not per type: on a large recorded corpus the uncached lookup was most
    of the run.

    The returned mapping is SHARED by every caller and must not be mutated; both
    collectors only read it.
    """
    return {f.encode_name: f for f in msgspec.structs.fields(struct)}


def _struct_name(struct: type[msgspec.Struct]) -> str:
    """*struct*'s name in a finding: ``Agg``, or ``ResultsEnvelope[Dividend]`` for a parametrized generic struct.

    A generic envelope is one class shared by many endpoints, so its bare name would pool every parametrization's
    findings under one key; the arguments keep each envelope's findings apart, as they were when each was its own class.
    """
    origin = get_origin(struct)
    if origin is None:
        return struct.__name__
    return f"{origin.__name__}[{', '.join(_struct_name(arg) for arg in get_args(struct))}]"


@cache
def _declared_names(struct: type[msgspec.Struct]) -> frozenset[str]:
    """``{"Struct.field"}`` for *struct*, cached on the type for the same reason."""
    return frozenset(f"{_struct_name(struct)}.{field.name}" for field in msgspec.structs.fields(struct))


@cache
def _shape(tp: object) -> tuple[str, type | None, tuple[object, ...]]:
    """``(kind, base, args)`` for annotation *tp*: which branch of :func:`_walk` it takes, cached on the annotation.

    A pure function of an immutable annotation, cached for the reason :func:`_by_wire` is: the walk asks per NODE, and
    ``get_origin``, ``get_args`` and the ABC ``issubclass`` checks otherwise run millions of times over the few hundred
    annotations a package declares. ``kind`` is ``"union"``, ``"mapping"``, ``"sequence"``, ``"struct"`` or ``"leaf"``.
    """
    origin = get_origin(tp)
    args = get_args(tp)
    if origin in _UNION_ORIGINS:
        return "union", None, args
    base = origin or tp
    if not isinstance(base, type):
        return "leaf", None, args
    if issubclass(base, Mapping):
        return "mapping", base, args
    # ``str``/``bytes`` are Sequences too; :func:`_walk`'s isinstance guard on the VALUE is what excludes them.
    if issubclass(base, (Sequence, AbstractSet)):
        return "sequence", base, args
    if issubclass(base, msgspec.Struct):
        return "struct", base, args
    return "leaf", base, args


def _walk(value: object, tp: object, visit: _Visitor) -> None:
    """Walk a runtime *value* against its declared annotation *tp*.

    Dispatch is **structural** — each annotation form is handled where it occurs,
    so a mapping nested under a list, a union, or another mapping is handled at
    the depth it actually appears rather than only at the top level.

    This is the single descent both directions share; *visit* is called at every
    struct node reached and decides what to record there.
    """
    kind, base, args = _shape(tp)

    # Union (``X | Y``, ``Optional[X]``) — distribute over the members. A value
    # that satisfies one member is reported against that member only.
    if kind == "union":
        for arg in args:
            _walk(value, arg, visit)
        return

    # Mapping — the KEYS are caller-defined data, never field names. Walk only
    # the VALUES, against the mapping's declared value type.
    if kind == "mapping":
        if isinstance(value, Mapping) and len(args) == 2:  # noqa: PLR2004 -- a mapping annotation has a key and a value argument
            for item in value.values():
                _walk(item, args[1], visit)
        return

    # Sequence / set container — walk each element against its element type.
    # ``str``/``bytes`` are Sequences too, but the isinstance guard below is what
    # excludes them: a string value is never one of the container types.
    #
    # ``json.loads`` yields only lists, so the tuple/set VALUE types are defensive; a ``tuple[...]`` ANNOTATION is
    # common, and its value still arrives as a list.
    if kind == "sequence":
        if isinstance(value, (list, tuple, set, frozenset)):
            for item, item_type in _elements(value, args):
                _walk(item, item_type, visit)
        return

    # A parametrized generic struct (``ResultsEnvelope[Dividend]``) is walked as itself, not as its origin: msgspec
    # resolves its fields against the arguments, where the bare origin's ``results`` is an unwalkable type variable.
    if kind == "struct" and base is not None and issubclass(base, msgspec.Struct):
        _walk_struct(value, typing.cast("type[msgspec.Struct]", tp) if args else base, visit)


def _elements(value: Iterable[object], args: tuple[object, ...]) -> list[tuple[object, object]]:
    """Pair each element of *value* with the annotation that governs it.

    Handles the three container spellings that occur: homogeneous (``list[X]``,
    ``tuple[X, ...]``) and the fixed-length heterogeneous tuple (``tuple[X, Y]``),
    where the element type is positional rather than shared.
    """
    items = list(value)
    if not args:
        return []
    homogeneous = len(args) == 1 or (len(args) == 2 and args[1] is Ellipsis)  # noqa: PLR2004 -- ``tuple[X, ...]`` is two arguments
    if homogeneous:
        return [(item, args[0]) for item in items]
    # Fixed-length heterogeneous tuple — pair positionally over the overlap.
    paired = list(zip(items, args, strict=False))
    # An element the annotation does not cover means the wire has drifted. There
    # is no governing type for it, so check it against every member: that
    # over-reports, which is the acceptable failure here. Skipping it would hide
    # a rogue key, the one outcome this helper must never produce.
    paired += [(item, arg) for item in items[len(args) :] for arg in args]
    return paired


def _walk_struct(value: object, struct: type[msgspec.Struct], visit: _Visitor) -> None:
    """Visit one mapping as *struct*, then descend into each declared field."""
    if isinstance(value, list) and struct.__struct_config__.array_like:
        # A positional row: read it as the mapping it stands for, with any position past the last field under a key
        # no field declares, so the truncation msgspec would perform is reported instead (see the module docstring).
        fields = msgspec.structs.fields(struct)
        value = {(fields[i].encode_name if i < len(fields) else f"[{i}]"): item for i, item in enumerate(value)}
    elif isinstance(value, list):
        # A bare JSON array of rows decoded against the row struct.
        for item in value:
            _walk_struct(item, struct, visit)
        return
    if not isinstance(value, Mapping):
        return

    by_wire = _by_wire(struct)
    visit(struct, value, by_wire)
    for key, item in value.items():
        field = by_wire.get(key)
        if field is not None:
            _walk(item, field.type, visit)


def undeclared_keys(raw: object, target: object) -> set[str]:
    """Keys present in *raw* that *target* (or a nested struct) does not declare.

    *target* is a decode target: either a ``msgspec.Struct`` type or any annotation
    :func:`headgate.msgspec.decode` accepts, so an endpoint returning a
    top-level JSON array can pass its ``list[Row]`` target verbatim rather than
    having to unwrap it first. The name matches :func:`unexercised_fields`, so a
    keyword caller can use one spelling across the pair.

    Returns ``{"StructName.key"}`` entries so a failure names where to look.
    A ``dict[str, X]`` field's keys are data and are never reported; its VALUES
    are still walked, so a struct nested inside a map is still checked — at any
    depth, and through lists, tuples and unions on the way down.

    The corollary is a second place green means "not looked at": an OBJECT
    arriving where a map is declared is invisible. ``dict[str, S]`` against
    ``{"a": 1, "ROGUE": 2}`` returns an empty set, because both keys read as map
    keys — i.e. as data. That is inherent to suppressing keys, not a defect, but
    it means a wire that changed from a map to an object reports nothing here.

    Matching is on the **wire** name (``FieldInfo.encode_name``), so a field
    carrying ``msgspec.field(name=...)`` is matched by the name the provider
    actually sends, not by its Python attribute name.

    An ``array_like=True`` row is read by position, and a position past its last
    field is reported as ``Struct.[i]`` (see the module docstring).
    """
    found: set[str] = set()

    def visit(struct_at: type[msgspec.Struct], mapping: Mapping[str, Any], by_wire: _ByWire) -> None:
        found.update(f"{_struct_name(struct_at)}.{key}" for key in mapping if key not in by_wire)

    _walk(raw, target, visit)
    return found


def unexercised_fields(payloads: Iterable[object], target: object) -> set[str]:
    """Return declared fields that NO payload populates with a non-null value.

    Returns ``{"StructName.field_name"}`` — the **Python field name**, deliberately
    asymmetric with :func:`undeclared_keys`, which returns wire names. The two
    answer different questions: one names what the vendor sent that we ignore, the
    other names what we declared that the fixtures never prove. A baseline entry keyed on
    the Python name is the one a reader can find in ``models.py``.

    An explicit wire ``null`` does **not** count as exercised. It proves the key
    exists; it does not prove the declared type parses the vendor's value, which
    is the thing a fixture is supposed to establish.

    Only structs the payloads actually **reach** contribute. A struct no payload
    ever touches would otherwise report its entire field list as unexercised —
    noise that pushes an author toward blanket baseline entries, which is how a gate gets
    allowlisted into uselessness.

    *target* accepts a generic decode target (``list[Row]``, ``dict[str, Row]``)
    exactly as :func:`undeclared_keys` does.

    An ``array_like=True`` row is read by position: a non-null position populates
    its field (see the module docstring).
    """
    reached: set[type[msgspec.Struct]] = set()
    exercised: set[str] = set()

    def visit(struct_at: type[msgspec.Struct], mapping: Mapping[str, Any], by_wire: _ByWire) -> None:
        reached.add(struct_at)
        for key, value in mapping.items():
            field = by_wire.get(key)
            if field is not None and value is not None:
                exercised.add(f"{_struct_name(struct_at)}.{field.name}")

    for payload in payloads:
        _walk(payload, target, visit)

    declared = {name for struct_at in reached for name in _declared_names(struct_at)}
    return declared - exercised


class Findings(NamedTuple):
    """A package's fidelity findings, or its recorded debt: the two compare with ``==``.

    ``undeclared`` holds wire keys no struct declares (:func:`undeclared_keys`), ``unexercised`` declared fields no
    payload populates (:func:`unexercised_fields`), each as ``"Struct.name"``.
    """

    undeclared: frozenset[str]
    unexercised: frozenset[str]


def findings(pairs: Iterable[tuple[object, object]]) -> Findings:
    """Both directions over *pairs*, each a ``(payload, decode target)``.

    The directions aggregate differently, and the difference is load-bearing. ``undeclared`` is the union over every
    payload: a key one body sends that its target does not declare is a drop on its own. ``unexercised`` is asked once
    per TARGET, over every payload decoded into it: one populated instance anywhere proves a field, so a struct shared
    by several endpoints is not reported for the fields only some of them fill.
    """
    undeclared: set[str] = set()
    by_target: dict[object, list[object]] = {}
    for payload, target in pairs:
        undeclared |= undeclared_keys(payload, target)
        by_target.setdefault(target, []).append(payload)
    unexercised = set[str]().union(*(unexercised_fields(payloads, target) for target, payloads in by_target.items()))
    return Findings(frozenset(undeclared), frozenset(unexercised))


#: The baseline's file name, beside a package's tests.
BASELINE_FILE = "_fidelity_baseline.toml"

#: What a recorded entry can be, and so what fixes it. Closed on purpose: the kinds have different remedies, and only
#: some are ours.
#:
#: * ``deliberate``: left out on purpose, for the reason given (off-spec, a derived field, a payload no caller reads).
#: * ``fixture-gap``: no capture populates the field yet; a better argument tuple or a fresh capture closes it.
#: * ``entitlement``: only a plan this account lacks would populate it.
#: * ``source-defect``: the struct is wrong (drops a key it should declare, declares one the wire never carries).
KINDS = frozenset({"deliberate", "fixture-gap", "entitlement", "source-defect"})

#: The kinds an undeclared key can be: the wire DID send it, so it was not a capture that fell short.
_UNDECLARED_KINDS = frozenset({"deliberate", "source-defect"})


def parse_baseline(text: str) -> Findings:
    """Parse ``_fidelity_baseline.toml`` text into :class:`Findings`.

    Rejects an unknown section and any entry missing its reason, ISO date or kind.
    """
    sections = tomllib.loads(text)
    if unknown := set(sections) - set(Findings._fields):
        msg = f"baseline sections are {list(Findings._fields)}, not {sorted(unknown)}"
        raise ValueError(msg)
    found: dict[str, frozenset[str]] = {}
    for direction in Findings._fields:
        entries = sections.get(direction, {})
        for key, meta in entries.items():
            if not isinstance(meta, dict):
                msg = f"baseline {direction}.{key} must be a table with a reason, an ISO date and a kind"
                raise TypeError(msg)
            reason = meta.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                msg = f"baseline {direction}.{key} needs a non-empty reason string"
                raise ValueError(msg)
            _check_iso_date(f"{direction}.{key}", meta.get("date"))
            kinds = _UNDECLARED_KINDS if direction == "undeclared" else KINDS
            if meta.get("kind") not in kinds:
                msg = f"baseline {direction}.{key} needs a kind, one of {sorted(kinds)}"
                raise ValueError(msg)
        found[direction] = frozenset(entries)
    return Findings(**found)


def _check_iso_date(key: str, value: object) -> None:
    """Require a quoted ``YYYY-MM-DD`` string, so ``rg 'date = "202'`` finds every entry.

    The type is checked explicitly rather than left to ``date.fromisoformat``, which
    raises ``TypeError`` on a non-string. Two shapes make that reachable: ``tomllib``
    decodes an UNQUOTED ``1979-05-27`` into a native ``datetime.date``, and
    ``date = 2026`` into an ``int`` — neither of which a grep for the date can find.
    """
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        msg = f'baseline {key} needs a quoted ISO date, e.g. date = "2026-08-15"'
        raise ValueError(msg)
    try:
        date.fromisoformat(value)
    except ValueError:
        msg = f"baseline {key} has an ISO-shaped but invalid date: {value!r}"
        raise ValueError(msg) from None


def wire_names(module: types.ModuleType) -> dict[str, dict[str, str]]:
    """``{StructName: {attribute: wire_key}}`` for every ``msgspec.Struct`` *module* defines.

    The wire contract of a client package as DATA, so a package can pin it in a syrupy
    snapshot and assert equality. Two
    moves need that proof and neither can get it from a decode test alone:

    * switching a struct from per-field ``msgspec.field(name=...)`` to ``rename="camel"`` —
      byte-identical only if every key comes out the same, which this shows key by key;
    * any later rename of an attribute on a ``rename="camel"`` struct — the wire key follows
      the attribute name SILENTLY (a missing key just takes the default), and only a pinned
      map notices.

    Reads ``FieldInfo.encode_name`` — the same wire-name index :func:`undeclared_keys`
    matches on — so the two helpers agree on what "the wire name" is. Only structs whose
    ``__module__`` is *module* count; re-exports from a sibling would pin another package's
    contract under this one's name.
    """
    return {
        name: {f.name: f.encode_name for f in msgspec.structs.fields(obj)}
        for name, obj in sorted(vars(module).items())
        if isinstance(obj, type) and issubclass(obj, msgspec.Struct) and obj.__module__ == module.__name__
    }


def load_baseline(tests_dir: Path | str) -> Findings:
    """Read ``_fidelity_baseline.toml`` from *tests_dir*, a package's test directory; a missing file records nothing.

    One table per direction, each entry keyed ``"Struct.name"`` and carrying a reason, a quoted ISO date and a
    :data:`KINDS` kind, so every entry stays greppable (``rg 'date = "202'``)::

        [undeclared]
        "Fill.is_rebalance" = { reason = "off-spec", date = "2026-11-02", kind = "deliberate" }

        [unexercised]
        "Agg.ticker" = { reason = "no capture populates it", date = "2026-11-05", kind = "fixture-gap" }

    The shape is **enforced** rather than documented: an undated entry is exactly the one that outlives its
    justification, and nothing else would notice.
    """
    path = Path(tests_dir) / BASELINE_FILE
    if not path.is_file():
        return Findings(frozenset(), frozenset())
    return parse_baseline(path.read_text(encoding="utf-8"))


def assert_matches_baseline(found: Findings, baseline: Findings) -> None:
    """Fail unless *found* is exactly *baseline*, naming each new finding and each stale entry."""
    lines: list[str] = []
    for direction in Findings._fields:
        live, recorded = getattr(found, direction), getattr(baseline, direction)
        lines += [f"NEW {direction}: {key}" for key in sorted(live - recorded)]
        lines += [
            f"STALE {direction} (nothing shows it any more, delete the entry): {key}" for key in sorted(recorded - live)
        ]
    if lines:
        msg = "the findings differ from _fidelity_baseline.toml:\n  " + "\n  ".join(lines)
        raise AssertionError(msg)
