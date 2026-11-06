# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the endpoint-manifest helper.

The manifest is the table three consumers read — the recorded tests (``test_recorded.py``), the
parametrized per-client `test_client.py`, and the exhaustiveness assertion that
fails when a new endpoint is added without being listed. A helper that silently
under-reports would defeat the third, so it gets its own tests.
"""

from typing import TYPE_CHECKING

import msgspec
import pytest
from headgate import AsyncBaseClient

from examples.msgspec.lda.client import LdaClient
from examples.pydantic.open_meteo.client import ForecastClient
from headgate_verify.testing.manifest import (
    Endpoint,
    manifest_drift,
    own_endpoint_methods,
    own_walk_methods,
    uncovered_methods,
    unlisted_methods,
)

if TYPE_CHECKING:
    from headgate import Paginated


class Row(msgspec.Struct, frozen=True):
    """A one-field row."""

    a: int


class FakeClient(AsyncBaseClient):
    """Stands in for a real client: two endpoints, a private helper, a property.

    The property is not decorative: a client's public property (a page size, a request cap) would be counted as an
    endpoint without the ``callable`` predicate.
    """

    async def list_things(self) -> list[Row]:
        """Stand in for a list endpoint."""
        raise NotImplementedError

    async def get_thing(self, thing_id: str) -> Row:
        """Stand in for a single read."""
        raise NotImplementedError

    async def _private_helper(self) -> None: ...

    @property
    def results(self) -> tuple[Row, ...]:
        """Return nothing: a property, not an endpoint."""
        return ()


LIST_THINGS = Endpoint(
    method="list_things",
    args=(),
    kwargs={},
    path="/v1/things",
    envelope=list[Row],
)
GET_THING = Endpoint(
    method="get_thing",
    args=("abc",),
    kwargs={},
    path="/v1/things/abc",
    envelope=Row,
)


def test_full_manifest_reports_nothing() -> None:
    """Full manifest reports nothing."""
    assert uncovered_methods(FakeClient, [LIST_THINGS, GET_THING]) == set()


def test_public_method_missing_from_the_manifest_is_reported() -> None:
    """Public method missing from the manifest is reported."""
    assert uncovered_methods(FakeClient, [LIST_THINGS]) == {"get_thing"}


def test_private_methods_are_not_endpoints() -> None:
    """Private methods are not endpoints."""
    assert "_private_helper" not in uncovered_methods(FakeClient, [])


def test_inherited_base_verbs_are_not_endpoints() -> None:
    """Every client inherits ``get``/``post``/``aclose``/… from ``AsyncBaseClient``."""
    assert uncovered_methods(FakeClient, []) == {"list_things", "get_thing"}


def test_a_new_base_class_verb_is_excluded_without_touching_this_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The exclusion set is DERIVED from ``AsyncBaseClient``, not copied from it.

    A hardcoded frozenset of today's seven verbs passes every other test in this
    file and fails only here — the day someone adds a verb to the base class, every
    client's exhaustiveness test would start demanding a manifest entry for it.
    """
    monkeypatch.setattr(AsyncBaseClient, "trace", lambda _self: None, raising=False)
    assert uncovered_methods(FakeClient, []) == {"list_things", "get_thing"}


def test_a_property_is_not_an_endpoint() -> None:
    """A ``property`` is a non-callable descriptor, so the predicate skips it."""
    assert "results" not in uncovered_methods(FakeClient, [])


def test_fixture_name_defaults_to_the_method_name() -> None:
    """Fixture name defaults to the method name."""
    assert LIST_THINGS.fixture_name == "list_things.json"


def test_fixture_name_honours_an_explicit_override() -> None:
    """Fixture name honours an explicit override."""
    endpoint = Endpoint(
        method="list_things",
        args=(),
        kwargs={},
        path="/v1/things",
        envelope=list[Row],
        fixture="things_page_two.json",
    )
    assert endpoint.fixture_name == "things_page_two.json"


def test_endpoint_is_frozen() -> None:
    """Endpoint is frozen."""
    with pytest.raises(AttributeError):
        LIST_THINGS.method = "nope"  # ty: ignore[invalid-assignment]  # the AttributeError IS the test


def test_paginated_defaults_to_false() -> None:
    """Paginated defaults to false."""
    assert LIST_THINGS.paginated is False


def test_the_lda_example_lists_every_read_walks_included() -> None:
    """Canary over a real client: lda's five walks are endpoints of their own, with no single-page sibling."""
    assert len(own_endpoint_methods(LdaClient)) == 18  # noqa: PLR2004 -- five walks, five reads, eight constants lists
    assert own_walk_methods(LdaClient) == {
        "get_clients",
        "get_contributions",
        "get_filings",
        "get_lobbyists",
        "get_registrants",
    }
    assert own_endpoint_methods(ForecastClient) == {"get_forecast"}


class WalkingClient(AsyncBaseClient):
    """A single-page read and the walk over the same path beside it."""

    async def get_things(self) -> list[Row]:
        """Stand in for the single page."""
        raise NotImplementedError

    def walk_things(self) -> Paginated[list[Row], Row]:
        """Stand in for the walk over the same path."""
        raise NotImplementedError


def test_a_walk_is_an_endpoint_by_default() -> None:
    """A walk is an endpoint by default."""
    assert uncovered_methods(WalkingClient, []) == {"get_things", "walk_things"}


def test_a_walk_beside_its_page_can_be_left_out() -> None:
    """``include_walks=False``: a walk whose page another method reads has no wire of its own to list."""
    assert own_walk_methods(WalkingClient) == {"walk_things"}
    assert uncovered_methods(WalkingClient, [], include_walks=False) == {"get_things"}
    things = Endpoint(method="get_things", path="/things", envelope=list[Row])
    assert manifest_drift(WalkingClient, [things], include_walks=False) == ""


# --- the mirror: manifest entries naming a method the client does not have ---


def test_stale_manifest_entry_is_reported() -> None:
    """``uncovered_methods`` is structurally blind here, as any one-way exhaustiveness check is."""
    gone = Endpoint(
        method="get_thing_v1",
        args=(),
        kwargs={},
        path="/v1/things/x",
        envelope=Row,
    )
    assert unlisted_methods(FakeClient, [LIST_THINGS, GET_THING, gone]) == {"get_thing_v1"}


def test_a_matching_manifest_has_no_stale_entries() -> None:
    """A matching manifest has no stale entries."""
    assert unlisted_methods(FakeClient, [LIST_THINGS, GET_THING]) == set()


def test_an_entry_naming_an_inherited_verb_is_not_called_missing() -> None:
    """``get`` exists on the client, so it is not a nonexistent method.

    It is simply not an endpoint, which is ``uncovered_methods``' concern rather than this one.
    """
    inherited = Endpoint(method="get", args=(), kwargs={}, path="/", envelope=Row)
    assert unlisted_methods(FakeClient, [inherited]) == set()


def test_manifest_drift_is_empty_when_the_manifest_matches() -> None:
    """Manifest drift is empty when the manifest matches."""
    assert manifest_drift(FakeClient, [LIST_THINGS, GET_THING]) == ""


def test_manifest_drift_reports_both_directions_with_remedies() -> None:
    """Manifest drift reports both directions with remedies."""
    gone = Endpoint(method="get_thing_v1", args=(), kwargs={}, path="/v1/x", envelope=Row)
    report = manifest_drift(FakeClient, [LIST_THINGS, gone])
    assert "get_thing" in report
    assert "get_thing_v1" in report
    # Each half must say what to DO, not merely name the symbol — both the primary
    # remedy and the "or else" that stops a reader hunting.
    assert "Add an Endpoint" in report
    assert "should be private" in report
    assert "RENAMED" in report
    assert "REMOVED" in report
    assert "delete the entry and its captured fixture" in report


def test_manifest_drift_accepts_a_one_shot_iterator() -> None:
    """It reads the manifest twice, so a generator must not be silently half-consumed.

    The manifest here carries a STALE entry on purpose: with a matching manifest both
    halves report nothing whether or not the iterator survives the first read, so that
    version of this test cannot tell the two apart. Only the second half's finding
    proves the iterator was not exhausted by the first.
    """
    gone = Endpoint(method="get_thing_v1", args=(), kwargs={}, path="/v1/x", envelope=Row)
    report = manifest_drift(FakeClient, iter([LIST_THINGS, GET_THING, gone]))
    assert "get_thing_v1" in report


def test_args_and_kwargs_default_to_empty() -> None:
    """Most entries need neither, so omitting them must work."""
    minimal = Endpoint(method="list_things", path="/v1/things", envelope=list[Row])
    assert minimal.args == ()
    assert minimal.kwargs == {}


def test_each_endpoint_gets_its_own_kwargs_dict() -> None:
    """``default_factory``, not a shared mutable default — the whole point of the shape."""
    first = Endpoint(method="list_things", path="/v1/things", envelope=list[Row])
    second = Endpoint(method="get_thing", path="/v1/things/x", envelope=Row)
    first.kwargs["leaked"] = True
    assert second.kwargs == {}
