# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Tests for the cassette reader: bodies by endpoint path, and a loud failure where there is nothing to read."""

from typing import TYPE_CHECKING

import pytest
import yaml

from headgate_verify.testing.cassettes import cassette_bodies, endpoint_bodies, endpoint_body, recorded_bodies
from headgate_verify.testing.manifest import Endpoint

if TYPE_CHECKING:
    from pathlib import Path


def _interaction(uri: str, body: str | bytes) -> dict[str, object]:
    return {
        "request": {"method": "GET", "uri": uri, "body": None, "headers": {}},
        "response": {"status": {"code": 200, "message": "OK"}, "headers": {}, "body": {"string": body}},
    }


def _cassette(path: Path, *interactions: dict[str, object]) -> Path:
    path.write_text(yaml.safe_dump({"version": 1, "interactions": list(interactions)}), encoding="utf-8")
    return path


@pytest.fixture
def cassette(tmp_path: Path) -> Path:
    """Return a cassette holding a token exchange and two reads of one endpoint."""
    return _cassette(
        tmp_path / "bars.yaml",
        _interaction("https://auth.example.test/oauth/token", '{"access_token": "<redacted>"}'),
        _interaction("https://api.example.test/v2/stocks/AAPL/bars?limit=2", '{"bars": []}'),
        _interaction("https://api.example.test/v2/stocks/MSFT/bars/", b'{"bars": [1]}'),
    )


def test_every_body_reads_back_in_recorded_order_as_bytes(cassette: Path) -> None:
    """Every body reads back in recorded order as bytes."""
    assert cassette_bodies(cassette) == [b'{"access_token": "<redacted>"}', b'{"bars": []}', b'{"bars": [1]}']


def test_a_template_matches_one_segment_per_hole_and_the_end_of_the_path(cassette: Path) -> None:
    """The token exchange is left out; a trailing slash on either side still matches."""
    assert endpoint_bodies(cassette, "/v2/stocks/{symbol}/bars/") == [b'{"bars": []}', b'{"bars": [1]}']
    with pytest.raises(ValueError, match=r"no response to /stocks/\{symbol\}"):
        endpoint_bodies(cassette, "/stocks/{symbol}")


def test_endpoint_body_requires_exactly_one(cassette: Path) -> None:
    """Endpoint body requires exactly one."""
    assert endpoint_body(cassette, "/oauth/token") == b'{"access_token": "<redacted>"}'
    with pytest.raises(ValueError, match="holds 2 responses"):
        endpoint_body(cassette, "/v2/stocks/{symbol}/bars")


@pytest.mark.parametrize("content", ["version: 1\ninteractions: []\n", "", "- not a mapping\n"])
def test_a_cassette_with_nothing_recorded_raises(tmp_path: Path, content: str) -> None:
    """A cassette with nothing recorded raises."""
    path = tmp_path / "empty.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match="holds no interactions"):
        cassette_bodies(path)


def test_a_missing_cassette_raises(tmp_path: Path) -> None:
    """A missing cassette raises."""
    with pytest.raises(FileNotFoundError):
        cassette_bodies(tmp_path / "absent.yaml")


def test_recorded_bodies_reads_the_endpoints_own_cassette(tmp_path: Path) -> None:
    """Recorded bodies reads the endpoints own cassette."""
    endpoint = Endpoint(method="get_filing", path="/filings/{uuid}/", envelope=object)
    _cassette(tmp_path / "test_endpoint[get_filing].yaml", _interaction("https://lda.gov/api/v1/filings/x/", "{}"))
    assert recorded_bodies(tmp_path, endpoint) == [b"{}"]
