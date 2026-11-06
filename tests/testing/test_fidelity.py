# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the fidelity walker itself.

The walker is the gate every client's ``test_models.py`` leans on, so it gets its
own tests: a helper that silently passes is worse than no helper.
"""

# NOT a TYPE_CHECKING import: msgspec resolves struct annotations at runtime, so
# `msgspec.structs.fields(WithAbstractMap)` raises NameError if `Mapping` is not a
# module global. Verified 2026-08-15 by moving it and watching fields() fail.
import types
from collections.abc import Mapping  # msgspec needs it at runtime, see above
from pathlib import Path
from typing import Literal

import msgspec
import pytest

from headgate_verify.testing.fidelity import (
    Findings,
    assert_matches_baseline,
    findings,
    load_baseline,
    parse_baseline,
    undeclared_keys,
    unexercised_fields,
    wire_names,
)


class Inner(msgspec.Struct, frozen=True):
    """A flat struct: one required field, one optional."""

    a: int
    b: str | None = None


class Outer(msgspec.Struct, frozen=True):
    """A struct holding ``Inner`` directly and in a list."""

    inner: Inner
    items: list[Inner] = []


def test_flat_struct_with_exact_keys_reports_nothing() -> None:
    """Flat struct with exact keys reports nothing."""
    assert undeclared_keys({"a": 1, "b": "x"}, Inner) == set()


def test_extra_key_is_reported_with_its_path() -> None:
    """Extra key is reported with its path."""
    assert undeclared_keys({"a": 1, "surprise": 2}, Inner) == {"Inner.surprise"}


def test_nested_extra_key_is_reported() -> None:
    """Nested extra key is reported."""
    raw = {"inner": {"a": 1, "nope": 2}, "items": []}
    assert undeclared_keys(raw, Outer) == {"Inner.nope"}


def test_extra_key_inside_a_list_element_is_reported() -> None:
    """Extra key inside a list element is reported."""
    raw = {"inner": {"a": 1}, "items": [{"a": 2}, {"a": 3, "boom": 4}]}
    assert undeclared_keys(raw, Outer) == {"Inner.boom"}


def test_dynamic_dict_keys_are_not_reported_as_undeclared() -> None:
    """A ``dict[str, X]`` field has caller-defined keys; they are data, not fields.

    Measured on massive: Polygon's sector map yields ``aerospace_and_defense``,
    ``banks``, ``biotechnology`` ... a name-only walker calls every one a dropped
    field. This is the refinement the spike surfaced.

    NOTE: this case is **vacuous on its own** — a ``float`` value reaches no Struct,
    so the walker never descends and this passes with or without key suppression.
    It is kept deliberately as the scalar-valued twin of
    ``test_dynamic_dict_with_struct_values_does_not_report_its_keys`` below, which
    is the discriminating one. If these are ever consolidated, keep THAT one.
    """

    class WithMap(msgspec.Struct, frozen=True):
        weights: dict[str, float]

    assert undeclared_keys({"weights": {"banks": 0.3, "energy": 0.7}}, WithMap) == set()


class MapValue(msgspec.Struct, frozen=True):
    """The value struct of a dynamic map."""

    a: int


class WithStructMap(msgspec.Struct, frozen=True):
    """A map whose keys are data and whose values are structs."""

    by_sector: dict[str, MapValue]


def test_dynamic_dict_with_struct_values_does_not_report_its_keys() -> None:
    """The discriminating case for the dynamic-mapping refinement.

    ``dict[str, float]`` (the test above) passes with or WITHOUT the refinement,
    because a float value reaches no Struct so the walker never descends. Only a
    map whose VALUES are structs separates the two behaviours: without the
    refinement the walker hands the whole map to ``MapValue`` and reports every
    sector name as a dropped field.
    """
    raw = {"by_sector": {"banks": {"a": 1}, "energy": {"a": 2}}}
    assert undeclared_keys(raw, WithStructMap) == set()


def test_struct_nested_inside_a_dynamic_map_is_still_checked() -> None:
    """Suppressing the KEYS must not stop the VALUES being walked."""
    raw = {"by_sector": {"banks": {"a": 1, "rogue": 2}}}
    assert undeclared_keys(raw, WithStructMap) == {"MapValue.rogue"}


def test_abstract_mapping_annotation_is_treated_as_dynamic() -> None:
    """The refinement keys off ``Mapping``, so ``Mapping[str, X]`` behaves like ``dict``."""

    class WithAbstractMap(msgspec.Struct, frozen=True):
        by_sector: Mapping[str, MapValue]

    assert undeclared_keys({"by_sector": {"banks": {"a": 1}}}, WithAbstractMap) == set()


class Deep(msgspec.Struct, frozen=True):
    """A one-field struct reached through containers."""

    a: int


class NestedContainers(msgspec.Struct, frozen=True):
    """Every container spelling that can sit between a field and a nested struct."""

    in_list: list[dict[str, Deep]] = []
    in_tuple: tuple[dict[str, Deep], ...] = ()
    in_map: dict[str, dict[str, Deep]] = {}
    in_union: Deep | dict[str, float] | None = None
    optional_map: dict[str, Deep] | None = None
    # Struct reachable only through a NON-FIRST union member. Every other union
    # field here puts the struct-bearing member first, where distributing over
    # the members and taking only ``args[0]`` give the same answer.
    struct_not_first: int | Deep | None = None


@pytest.mark.parametrize(
    ("field", "payload"),
    [
        ("in_list", [{"k": {"a": 1, "ROGUE": 2}}]),
        # Two elements, rogue in the SECOND: a variadic tuple must treat every
        # element as the same type. Pairing positionally against
        # ``(dict[str, Deep], Ellipsis)`` would walk element 1 against ``Ellipsis``
        # and miss it, which a single-element payload cannot detect.
        ("in_tuple", [{"k": {"a": 1}}, {"k": {"a": 1, "ROGUE": 2}}]),
        ("in_map", {"outer": {"inner": {"a": 1, "ROGUE": 2}}}),
        ("in_union", {"a": 1, "ROGUE": 2}),
        ("optional_map", {"k": {"a": 1, "ROGUE": 2}}),
        # Separates "distribute over every union member" from "take args[0]":
        # the struct sits behind ``int``, so only the former finds the rogue key.
        ("struct_not_first", {"a": 1, "ROGUE": 2}),
    ],
)
def test_rogue_key_is_found_through_any_container_nesting(field: str, payload: object) -> None:
    """A struct is reachable through lists, tuples, unions and nested maps.

    ``{"results": [{"AAPL": {...}, "MSFT": {...}}]}`` — a ``list[dict[str, Row]]`` —
    is an ordinary provider shape. A walker that only handles a mapping at the top
    of the annotation never descends here and reports a clean subtree forever,
    which is the "green while checking nothing" mode this module exists to prevent.
    """
    assert undeclared_keys({field: payload}, NestedContainers) == {"Deep.ROGUE"}


def test_nested_map_keys_are_not_reported_at_any_depth() -> None:
    """Suppression must apply at EVERY mapping level, not just the outermost.

    Handling only one level reports the inner map's key (``inner``) as a dropped
    field of ``Deep`` — a false positive on top of the false negative above.
    """
    assert undeclared_keys({"in_map": {"outer": {"inner": {"a": 1}}}}, NestedContainers) == set()


class Other(msgspec.Struct, frozen=True):
    """A second one-field struct, for positional tuples."""

    z: int


class HeterogeneousTuple(msgspec.Struct, frozen=True):
    """``tuple[X, Y]`` is positional, not homogeneous — ``ofr.OfrFsiSeries.data`` is live."""

    pair: tuple[Deep, Other]


def test_heterogeneous_tuple_elements_pair_positionally() -> None:
    """Element 0 is governed by ``Deep`` alone, so ``Other`` is not falsely blamed."""
    raw = {"pair": [{"a": 1, "ROGUE": 2}, {"z": 3}]}
    assert undeclared_keys(raw, HeterogeneousTuple) == {"Deep.ROGUE"}


def test_short_tuple_pairs_over_the_overlap_without_blaming_the_missing_member() -> None:
    """A short wire still pairs positionally, so ``Other`` is not dragged in.

    Checking the lone element against every member instead would also report
    ``Other.a`` and ``Other.ROGUE`` — noise that buries the one real finding.
    """
    raw = {"pair": [{"a": 1, "ROGUE": 2}]}
    assert undeclared_keys(raw, HeterogeneousTuple) == {"Deep.ROGUE"}


def test_over_long_tuple_still_surfaces_a_rogue_key_in_the_uncovered_element() -> None:
    """An element past the annotation has no governing type — over-report, never skip."""
    raw = {"pair": [{"a": 1}, {"z": 2}, {"ROGUE": 3}]}
    assert undeclared_keys(raw, HeterogeneousTuple) == {"Deep.ROGUE", "Other.ROGUE"}


def test_bare_top_level_array_is_walked_against_the_row_struct() -> None:
    """A provider returning a top-level JSON array, decoded as ``list[Row]``."""
    assert undeclared_keys([{"a": 1}, {"a": 2, "ROGUE": 3}], Deep) == {"Deep.ROGUE"}


def test_a_generic_decode_target_is_accepted_verbatim() -> None:
    """``expect=decoder(list[Row])`` is how array endpoints declare their target.

    A per-client suite reads that target off the client and passes it straight in
    (``an array endpoint`` is live), so rejecting a generic alias would make
    the gate unusable for every array-returning endpoint.
    """
    assert undeclared_keys([{"a": 1}, {"a": 2, "ROGUE": 3}], list[Deep]) == {"Deep.ROGUE"}
    assert undeclared_keys({"k": {"a": 1, "ROGUE": 2}}, dict[str, Deep]) == {"Deep.ROGUE"}


class WithLiteral(msgspec.Struct, frozen=True):
    """A ``Literal`` field, common on an enumerated wire value."""

    stop_direction: Literal["up", "down"]


def test_literal_annotated_field_is_walked_without_crashing() -> None:
    """A ``Literal`` is not a class, so the walk must not hand it to ``issubclass``.

    Dropping the non-type guard raises ``TypeError: issubclass() arg 1 must be a
    class`` here — a crash rather than a silent miss, but it would take down the
    whole suite of any client carrying one.
    """
    assert undeclared_keys({"stop_direction": "up", "ROGUE": 1}, WithLiteral) == {"WithLiteral.ROGUE"}


def test_renamed_field_matches_on_the_wire_name() -> None:
    """Renamed field matches on the wire name."""

    class Renamed(msgspec.Struct, frozen=True):
        volume: int = msgspec.field(name="v")

    assert undeclared_keys({"v": 10}, Renamed) == set()
    assert undeclared_keys({"volume": 10}, Renamed) == {"Renamed.volume"}


# --- direction two: declared fields no payload exercises ---------------------
#
# The discriminating construction for this direction: every nested struct below
# has TWO fields with only ONE populated. A walker that fails to descend leaves
# the struct unreachable and reports NOTHING, which is indistinguishable from
# "descended and found everything exercised" if the struct has a single field.
# Asserting the exact unexercised field proves the descent happened.


class Two(msgspec.Struct, frozen=True):
    """Two fields, one optional: proves a descent by naming the one left unfilled."""

    a: int
    b: int | None = None


class HostList(msgspec.Struct, frozen=True):
    """``Two`` behind a list of maps."""

    m: list[dict[str, Two]]


class HostTuple(msgspec.Struct, frozen=True):
    """``Two`` behind a variadic tuple of maps."""

    m: tuple[dict[str, Two], ...]


class HostMap(msgspec.Struct, frozen=True):
    """``Two`` behind a map of maps."""

    m: dict[str, dict[str, Two]]


class HostUnion(msgspec.Struct, frozen=True):
    """``Two`` as the first member of a union."""

    m: Two | dict[str, float] | None


class HostOptionalMap(msgspec.Struct, frozen=True):
    """``Two`` behind an optional map."""

    m: dict[str, Two] | None


class HostStructNotFirst(msgspec.Struct, frozen=True):
    """``Two`` behind a non-first union member."""

    m: int | Two | None


class Unreached(msgspec.Struct, frozen=True):
    """A struct no payload reaches."""

    never: int


class HostWithUnreached(msgspec.Struct, frozen=True):
    """A reached struct beside one no payload fills."""

    seen: Two
    missing: Unreached | None = None


def test_field_populated_in_one_payload_of_several_is_exercised() -> None:
    """Field populated in one payload of several is exercised."""
    payloads = [{"a": 1}, {"a": 2, "b": 3}, {"a": 4}]
    assert unexercised_fields(payloads, Two) == set()


def test_field_absent_from_every_payload_is_reported() -> None:
    """Field absent from every payload is reported."""
    assert unexercised_fields([{"a": 1}, {"a": 2}], Two) == {"Two.b"}


def test_explicit_null_does_not_count_as_exercised() -> None:
    """A wire ``null`` proves the KEY exists; it does not prove the declared type parses."""
    assert unexercised_fields([{"a": 1, "b": None}], Two) == {"Two.b"}


def test_nested_struct_fields_are_reached() -> None:
    """Nested struct fields are reached."""

    class Host(msgspec.Struct, frozen=True):
        inner: Two

    assert unexercised_fields([{"inner": {"a": 1}}], Host) == {"Two.b"}


@pytest.mark.parametrize(
    ("host", "payload"),
    [
        (HostList, {"m": [{"k": {"a": 1}}]}),
        (HostTuple, {"m": [{"k": {"a": 1}}, {"k": {"a": 1}}]}),
        (HostMap, {"m": {"outer": {"inner": {"a": 1}}}}),
        (HostUnion, {"m": {"a": 1}}),
        (HostOptionalMap, {"m": {"k": {"a": 1}}}),
        (HostStructNotFirst, {"m": {"a": 1}}),
    ],
)
def test_nested_struct_is_reached_through_every_container_shape(host: type, payload: object) -> None:
    """The five C1 shapes, plus the non-first union member, in direction two.

    A missed subtree here reads as "we need more fixtures" rather than "the tool
    is broken", so it would generate baseline entries for fields that are actually fine,
    and those entries would hide real findings.
    """
    assert unexercised_fields([payload], host) == {"Two.b"}


def test_struct_unreachable_from_any_payload_is_not_reported() -> None:
    """Only structs the payloads actually reach count toward the declared set.

    ``Unreached.never`` must NOT appear: reporting the full field list of a struct
    no payload touches is the noise that drives an author to blanket baseline entries.
    """
    assert unexercised_fields([{"seen": {"a": 1}}], HostWithUnreached) == {
        "HostWithUnreached.missing",
        "Two.b",
    }


def test_reports_the_python_field_name_not_the_wire_name() -> None:
    """Deliberately asymmetric with ``undeclared_keys``, which reports wire names."""

    class Renamed(msgspec.Struct, frozen=True):
        volume: int = msgspec.field(name="v")
        other: int | None = None

    assert unexercised_fields([{"v": 10}], Renamed) == {"Renamed.other"}
    # Nothing exercised: the report still names ``volume``, never the wire's ``v``.
    assert unexercised_fields([{}], Renamed) == {"Renamed.volume", "Renamed.other"}


def test_generic_decode_targets_are_accepted() -> None:
    """Generic decode targets are accepted."""
    assert unexercised_fields([[{"a": 1}, {"a": 2}]], list[Two]) == {"Two.b"}
    assert unexercised_fields([{"k": {"a": 1}}], dict[str, Two]) == {"Two.b"}


def test_no_payloads_reaches_nothing_and_reports_nothing() -> None:
    """No payloads reaches nothing and reports nothing."""
    assert unexercised_fields([], Two) == set()


# --- the recorded baseline -------------------------------------------------

_ENTRY = 'reason = "r", date = "2026-08-15", kind = "deliberate"'


def test_baseline_round_trip(tmp_path: Path) -> None:
    """Baseline round trip."""
    (tmp_path / "_fidelity_baseline.toml").write_text(
        "[undeclared]\n"
        '"TickerDetails.delisted_utc" = { reason = "delisted only", date = "2026-08-15", kind = "deliberate" }\n'
        "[unexercised]\n"
        '"Two.b" = { reason = "no capture fills it", date = "2026-08-15", kind = "fixture-gap" }\n'
    )
    assert load_baseline(tmp_path) == Findings(frozenset({"TickerDetails.delisted_utc"}), frozenset({"Two.b"}))


def test_missing_baseline_file_records_nothing_rather_than_raising() -> None:
    """Missing baseline file records nothing rather than raising."""
    assert load_baseline(Path("/nonexistent/tests/dir")) == Findings(frozenset(), frozenset())


def test_baseline_entry_without_a_reason_date_or_kind_is_rejected() -> None:
    """Each entry carries a reason, a date and a kind.

    A stale entry must be greppable, and nothing enforces that unless loading does.
    """
    for body in (
        '[undeclared]\n"Two.b" = { date = "2026-08-15", kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "because", kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "because", date = "2026-08-15" }\n',
        '[undeclared]\n"Two.b" = { reason = "because", date = "2026-08-15", kind = "someday" }\n',
    ):
        with pytest.raises(ValueError, match=r"undeclared\.Two\.b"):
            parse_baseline(body)


def test_an_undeclared_key_cannot_be_filed_as_a_fixture_gap() -> None:
    """The wire DID send an undeclared key, so "we did not capture enough" is the one reason it cannot have."""
    with pytest.raises(ValueError, match=r"undeclared\.Two\.b"):
        parse_baseline('[undeclared]\n"Two.b" = { reason = "r", date = "2026-08-15", kind = "fixture-gap" }\n')


def test_an_unknown_section_is_rejected() -> None:
    """``[waivers]`` or a typo'd direction would otherwise record nothing, and the entries under it would hide."""
    with pytest.raises(ValueError, match="waivers"):
        parse_baseline(f'[waivers]\n"Two.b" = {{ {_ENTRY} }}\n')


def test_baseline_entry_that_is_not_a_table_is_rejected_cleanly() -> None:
    """``"Two.b" = true`` is the shortest way to write an entry, and the wrong one.

    Without the table check this raises ``AttributeError`` from ``.get`` rather
    than naming the offending entry: an unhelpful failure for the one person
    who most needs to be told what to write instead.
    """
    with pytest.raises(TypeError, match=r"undeclared\.Two\.b"):
        parse_baseline('[undeclared]\n"Two.b" = true\n')


def test_a_baseline_mismatch_names_each_new_finding_and_each_stale_entry() -> None:
    """A baseline mismatch names each new finding and each stale entry."""
    found = Findings(frozenset({"Two.new"}), frozenset())
    recorded = Findings(frozenset(), frozenset({"Two.b"}))

    with pytest.raises(AssertionError, match=r"(?s)NEW undeclared: Two\.new.*STALE unexercised.*Two\.b"):
        assert_matches_baseline(found, recorded)
    assert_matches_baseline(recorded, recorded)


def test_findings_judge_unexercised_per_target_over_every_payload() -> None:
    """One populated instance anywhere proves a field.

    Two payloads into one target that each fill half of it leave nothing unexercised, while either alone would report
    the other half.
    """
    pairs = [({"a": 1}, Two), ({"a": 2, "b": "x", "rogue": 0}, Two)]

    assert findings(pairs) == Findings(frozenset({"Two.rogue"}), frozenset())
    assert findings(pairs[:1]) == Findings(frozenset(), frozenset({"Two.b"}))


# --- positional rows ----------------------------------------------------------


class Point(msgspec.Struct, frozen=True, array_like=True):
    """A positional row: ``[t, v]``."""

    t: int
    v: float | None = None


class HostPoints(msgspec.Struct, frozen=True):
    """A list of positional rows."""

    points: list[Point] = []


def test_a_positional_row_longer_than_its_struct_reports_each_extra_position() -> None:
    """An over-long ``array_like`` row is truncated without a word, so the walk must say what it would drop."""
    assert msgspec.json.decode(b"[1, 2.0, 3]", type=Point) == Point(1, 2.0)
    assert undeclared_keys({"points": [[1, 2.0, 3, 4]]}, HostPoints) == {"Point.[2]", "Point.[3]"}
    assert undeclared_keys({"points": [[1, 2.0], [1]]}, HostPoints) == set()


def test_a_positional_row_populates_its_fields_by_position() -> None:
    """A positional row populates its fields by position."""
    assert unexercised_fields([[[1, None]]], list[Point]) == {"Point.v"}
    assert unexercised_fields([[[1, None], [2, 0.5]]], list[Point]) == set()


class HostNullableStruct(msgspec.Struct, frozen=True):
    """An optional nested struct."""

    m: Two | None = None


class HostRows(msgspec.Struct, frozen=True):
    """A list of rows that may arrive empty."""

    rows: list[Two] = []


class Falsy(msgspec.Struct, frozen=True):
    """Fields whose populated values can be falsy."""

    flag: bool | None = None
    n: int | None = None
    s: str | None = None
    xs: list[int] | None = None


def test_null_sub_object_does_not_mark_its_struct_reached() -> None:
    """An explicit ``null`` where a struct is declared must not dump its field list.

    This is the reachability failure that survives a branch-predicate sweep: moving
    the ``visit`` call across the mapping guard (rather than deleting it) reports
    ``Two.a``/``Two.b`` for a sub-object the payload never contained. A reader would
    conclude "we need more fixtures", add fixtures for a sub-object the endpoint
    never returns populated, and eventually record fields that were never wrong.
    Optional null sub-objects are the common case in vendor payloads.
    """
    assert unexercised_fields([{"m": None}], HostNullableStruct) == {"HostNullableStruct.m"}


def test_falsy_but_present_values_count_as_exercised() -> None:
    """``False``/``0``/``""``/``[]`` are values the vendor sent, not absences.

    Measured over the client corpus: 82 fields are exercised ONLY by a falsy
    non-null value, so confusing "falsy" with "missing" moves the findings by
    ~10%. Boolean-heavy config structs are where this would drift.
    """
    assert unexercised_fields([{"flag": False, "n": 0, "s": "", "xs": []}], Falsy) == set()


def test_bare_top_level_array_is_walked_in_direction_two() -> None:
    """The bare-list arm of ``_walk_struct``; ``list[Two]`` routes through ``_walk`` instead."""
    assert unexercised_fields([[{"a": 1}]], Two) == {"Two.b"}


def test_empty_list_exercises_the_field_but_reaches_no_rows() -> None:
    """``rows`` itself is exercised (``[]`` is a value the vendor sent), while ``Two`` is never reached.

    So its fields are correctly absent rather than all reported.
    """
    assert unexercised_fields([{"rows": []}], HostRows) == set()


def test_empty_mapping_marks_the_struct_reached_with_everything_unexercised() -> None:
    """Empty mapping marks the struct reached with everything unexercised."""
    assert unexercised_fields([{}], Two) == {"Two.a", "Two.b"}


def test_array_where_a_map_is_declared_does_not_crash() -> None:
    """Object-to-array drift is what this tool exists to catch, so the gate must survive it.

    It must not raise ``AttributeError`` from ``.values()``.
    """
    # ``m`` is exercised (a non-null value arrived); the point is that walking a
    # list where a Mapping is declared returns cleanly instead of raising.
    assert unexercised_fields([{"m": [1, 2]}], HostOptionalMap) == set()
    assert undeclared_keys({"m": [1, 2]}, HostOptionalMap) == set()


@pytest.mark.parametrize(
    "body",
    [
        '[undeclared]\n"Two.b" = { reason = "r", date = "soon", kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "r", date = 2026, kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "r", date = 1979-05-27, kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "r", date = "2026-13-45", kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = true, date = "2026-08-15", kind = "deliberate" }\n',
        '[undeclared]\n"Two.b" = { reason = "   ", date = "2026-08-15", kind = "deliberate" }\n',
    ],
)
def test_baseline_entry_with_an_unusable_reason_or_date_is_rejected(body: str) -> None:
    """Greppability is the whole justification for the strictness.

    ``rg 'date = "202'`` finds nothing in a file where someone wrote ``date = "soon"``,
    and ``tomllib`` turns an UNQUOTED ``1979-05-27`` into a native ``datetime.date``
    that no grep for the string can see.
    """
    with pytest.raises(ValueError, match=r"Two\.b"):
        parse_baseline(body)


class HostBareDict(msgspec.Struct, frozen=True):
    """A ``dict`` field with no type arguments."""

    # The missing type argument IS the shape under test — the walker must handle an
    # annotation carrying no value type — so the warning is suppressed, not fixed.
    m: dict = {}  # ty: ignore[missing-type-argument]  # the bare annotation IS the shape under test


def test_bare_dict_annotation_has_no_value_type_to_walk() -> None:
    """``dict`` without type args carries no value annotation, so there is nothing below it to descend into.

    Indexing its (empty) args would raise.
    """
    assert unexercised_fields([{"m": {"k": 1}}], HostBareDict) == set()
    assert undeclared_keys({"m": {"k": 1}}, HostBareDict) == set()


def test_iso_basic_format_date_is_rejected() -> None:
    """``date.fromisoformat`` accepts ``20260815``, but the documented and greppable shape is ``YYYY-MM-DD``.

    That is why the pattern is checked separately rather than left to the parser.
    """
    with pytest.raises(ValueError, match=r"Two\.b"):
        parse_baseline('[undeclared]\n"Two.b" = { reason = "r", date = "20260815", kind = "deliberate" }\n')


# --- generic envelopes and the wire-name map ------------------------------------


class Envelope[T](msgspec.Struct, frozen=True):
    """A generic envelope, parametrized per endpoint."""

    results: list[T]


class Dividend(msgspec.Struct, frozen=True):
    """An envelope's row."""

    amount: float


def test_a_generic_envelope_is_named_with_its_arguments() -> None:
    """Each parametrization keeps its own findings rather than pooling them under ``Envelope``."""
    assert undeclared_keys({"results": [{"amount": 1.0, "x": 1}], "status": "OK"}, Envelope[Dividend]) == {
        "Envelope[Dividend].status",
        "Dividend.x",
    }


class HostBareList(msgspec.Struct, frozen=True):
    """A ``list`` field with no type arguments."""

    m: list = []  # ty: ignore[missing-type-argument]  # the bare annotation IS the shape under test


def test_bare_list_annotation_has_no_element_type_to_walk() -> None:
    """Bare list annotation has no element type to walk."""
    assert undeclared_keys({"m": [{"rogue": 1}]}, HostBareList) == set()


def test_wire_names_maps_each_struct_of_the_module_to_its_wire_keys() -> None:
    """Wire names maps each struct of the module to its wire keys."""
    module = types.ModuleType("wire_demo")

    class Bar(msgspec.Struct, rename="camel"):
        open_price: float
        volume: int = msgspec.field(name="v")

    Bar.__module__ = "wire_demo"
    module.Bar = Bar  # ty: ignore[unresolved-attribute]  # a module built at run time
    module.Envelope = Envelope  # ty: ignore[unresolved-attribute]  # defined elsewhere: not this module's contract
    module.n = 1  # ty: ignore[unresolved-attribute]  # not a struct
    assert wire_names(module) == {"Bar": {"open_price": "openPrice", "volume": "v"}}
