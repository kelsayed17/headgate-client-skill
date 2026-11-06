# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Read what a vcrpy cassette recorded, so the fidelity walk and the replay-based tests can read a recorded wire.

A cassette (``tests/cassettes/<module>/<test>.yaml``) is what pytest-recording writes when a test marked ``vcr`` runs
with ``--record-mode`` set (:mod:`headgate_verify.testing.recording`), and replays when it is not. Each interaction
keeps the request and the response the client consumed; with ``decode_compressed_response`` the bodies are stored
decoded, so they read back as the JSON the provider sent.

Each reader raises rather than returning nothing for a missing, empty or unmatched cassette: a fidelity check over no
bodies passes whatever the wire sent.
"""

import re
from functools import cache
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

import yaml

if TYPE_CHECKING:
    import pathlib

    from headgate_verify.testing.manifest import Endpoint

__all__ = ["cassette_bodies", "endpoint_bodies", "endpoint_body", "recorded_bodies"]

# libyaml's safe loader when PyYAML was built with it: the pure-Python one takes seconds over megabytes of cassettes.
_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


@cache
def _interactions(path: pathlib.Path) -> tuple[dict[str, Any], ...]:
    """Parse the cassette's interactions once per process."""
    loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=_LOADER)  # noqa: S506 -- a safe loader, C or pure Python
    interactions = tuple(loaded.get("interactions") or ()) if isinstance(loaded, dict) else ()
    if not interactions:
        msg = f"cassette {path} holds no interactions; re-record it"
        raise ValueError(msg)
    return interactions


def _body(interaction: dict[str, Any]) -> bytes:
    raw = interaction["response"]["body"]["string"]
    return raw if isinstance(raw, bytes) else str(raw).encode()


def cassette_bodies(path: pathlib.Path) -> list[bytes]:
    """Return every response body in the cassette at *path*, in the order it was recorded."""
    return [_body(interaction) for interaction in _interactions(path)]


def endpoint_bodies(path: pathlib.Path, template: str) -> list[bytes]:
    """Return the bodies in the cassette at *path* answering requests to the endpoint path *template*.

    *template* is a manifest's ``path`` (``/v2/stocks/{symbol}/bars``): each ``{name}`` matches one path segment, and
    the URL path must END with it, since a client's base URL may carry a prefix. A cassette also holds requests an
    endpoint needs but is not (a token exchange), and those are left out.
    """
    pattern = re.compile(re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(template.rstrip("/"))) + "/?$")
    bodies = [
        _body(interaction)
        for interaction in _interactions(path)
        if pattern.search(urlsplit(interaction["request"]["uri"]).path)
    ]
    if not bodies:
        msg = f"cassette {path} holds no response to {template}; re-record it"
        raise ValueError(msg)
    return bodies


def endpoint_body(path: pathlib.Path, template: str) -> bytes:
    """Return the ONE body in the cassette at *path* answering *template*: what a replay-based test serves."""
    bodies = endpoint_bodies(path, template)
    if len(bodies) != 1:
        msg = f"cassette {path} holds {len(bodies)} responses to {template}, not one"
        raise ValueError(msg)
    return bodies[0]


def recorded_bodies(cassettes: pathlib.Path, endpoint: Endpoint) -> list[bytes]:
    """Return the bodies *endpoint*'s own recording holds for its path, from ``test_endpoint[<method>].yaml``.

    The name is the one :func:`headgate_verify.testing.recording.recorded` gives each endpoint's test when the
    recorded test is ``test_endpoint``, so a package's recorded test module and its fidelity test agree on it without
    either spelling a file name.
    """
    return endpoint_bodies(cassettes / f"test_endpoint[{endpoint.method}].yaml", endpoint.path)
