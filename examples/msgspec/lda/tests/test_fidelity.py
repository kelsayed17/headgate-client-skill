# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The lda.gov wire against the structs it decodes into: every endpoint listed, every recorded key declared.

``MANIFEST`` lists each endpoint the client has, with the decode target its reader declares (``FILINGS`` decodes
``Page[Filing]``). ``manifest_drift`` fails when an endpoint is added without an entry, and ``findings`` walks each
recorded body against its entry's target. What the structs knowingly leave out is ``_fidelity_baseline.toml`` beside
this file, compared for exact equality, so a new key lda.gov sends fails here and an entry nothing shows any more does
too.
"""

import json
from pathlib import Path

import pytest

from examples.msgspec.lda.client import LdaClient
from examples.msgspec.lda.models import (
    Client,
    Constant,
    ContributionReport,
    Filing,
    GovernmentEntity,
    LobbyistWithRegistrant,
    Page,
    Registrant,
)
from headgate_verify.testing.fidelity import assert_matches_baseline, findings, load_baseline
from headgate_verify.testing.manifest import Endpoint, manifest_drift

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"


def _constants(method: str, path: str, envelope: object = list[Constant]) -> Endpoint:
    return Endpoint(method=method, path=path, envelope=envelope, fixture=f"{method.removeprefix('get_')}.json")


MANIFEST = [
    Endpoint(method="get_filings", path="/filings/", envelope=Page[Filing], paginated=True, fixture="filings.json"),
    Endpoint(method="get_filing", path="/filings/{filing_uuid}/", envelope=Filing, fixture="filing.json"),
    Endpoint(
        method="get_contributions",
        path="/contributions/",
        envelope=Page[ContributionReport],
        paginated=True,
        fixture="contributions.json",
    ),
    Endpoint(
        method="get_contribution",
        path="/contributions/{filing_uuid}/",
        envelope=ContributionReport,
        fixture="contribution.json",
    ),
    Endpoint(
        method="get_registrants",
        path="/registrants/",
        envelope=Page[Registrant],
        paginated=True,
        fixture="registrants.json",
    ),
    Endpoint(
        method="get_registrant", path="/registrants/{registrant_id}/", envelope=Registrant, fixture="registrant.json"
    ),
    Endpoint(method="get_clients", path="/clients/", envelope=Page[Client], paginated=True, fixture="clients.json"),
    Endpoint(method="get_client", path="/clients/{client_id}/", envelope=Client, fixture="client.json"),
    Endpoint(
        method="get_lobbyists",
        path="/lobbyists/",
        envelope=Page[LobbyistWithRegistrant],
        paginated=True,
        fixture="lobbyists.json",
    ),
    Endpoint(
        method="get_lobbyist",
        path="/lobbyists/{lobbyist_id}/",
        envelope=LobbyistWithRegistrant,
        fixture="lobbyist.json",
    ),
    _constants("get_constants_filing_filingtypes", "/constants/filing/filingtypes/"),
    _constants("get_constants_filing_lobbyingactivityissues", "/constants/filing/lobbyingactivityissues/"),
    _constants(
        "get_constants_filing_governmententities",
        "/constants/filing/governmententities/",
        list[GovernmentEntity],
    ),
    _constants("get_constants_general_countries", "/constants/general/countries/"),
    _constants("get_constants_general_states", "/constants/general/states/"),
    _constants("get_constants_lobbyist_prefixes", "/constants/lobbyist/prefixes/"),
    _constants("get_constants_lobbyist_suffixes", "/constants/lobbyist/suffixes/"),
    _constants("get_constants_contribution_itemtypes", "/constants/contribution/itemtypes/"),
]

#: Recorded bodies beyond each endpoint's own fixture: an empty page and the two pages of a walk.
EXTRA_BODIES = [
    ("filings_empty.json", Page[Filing]),
    ("lobbyists_walk_page_1.json", Page[LobbyistWithRegistrant]),
    ("lobbyists_walk_page_2.json", Page[LobbyistWithRegistrant]),
]


def _read(fixture: str) -> object:
    return json.loads((FIXTURES / fixture).read_bytes())


def test_the_manifest_lists_every_endpoint() -> None:
    """The manifest lists every endpoint."""
    if report := manifest_drift(LdaClient, MANIFEST):
        pytest.fail(report)


def test_every_recorded_body_matches_the_structs_and_the_baseline() -> None:
    """Every recorded body matches the structs and the baseline."""
    pairs = [(_read(endpoint.fixture_name), endpoint.envelope) for endpoint in MANIFEST]
    pairs += [(_read(fixture), target) for fixture, target in EXTRA_BODIES]
    assert_matches_baseline(findings(pairs), load_baseline(HERE))
