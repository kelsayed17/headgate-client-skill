# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Endpoint manifests: one table per client, read by its recording, its client tests and an exhaustiveness check.

A headgate client is uniform by construction: every method is ``self.get(t"path", expect=decoder(Envelope), ...)``
or the ``self.paginate(...)`` walk over one. That uniformity lets ONE table of :class:`Endpoint` drive

1. the recorded test (:mod:`headgate_verify.testing.recording`): what to record live, with which arguments;
2. the parametrized client tests: path, params, headers and decoded shape;
3. the fidelity walk (:mod:`headgate_verify.testing.fidelity`): each recorded body against its ``envelope``;
4. :func:`manifest_drift`: a new endpoint fails the suite until it is listed, and a stale entry until it is removed.

Why runtime inspection, not grep or AST
---------------------------------------
A file-scoped grep for ``def`` cannot tell the client class from a protocol or helper class sharing its file, and
``class`` counts ``TypedDict`` parameter classes as models. Inspecting the class itself has neither problem. The
``callable`` predicate matters too: a ``property`` is a non-callable descriptor, so ``inspect.getmembers(cls,
callable)`` skips it, and a client's public property (a page size, a request cap) is never counted as an endpoint.
"""

import inspect
from annotationlib import Format
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

from headgate import AsyncBaseClient

__all__ = [
    "Endpoint",
    "manifest_drift",
    "own_endpoint_methods",
    "own_walk_methods",
    "uncovered_methods",
    "unlisted_methods",
]


@dataclass(frozen=True, kw_only=True)
class Endpoint:
    """One client method, and everything three consumers need to exercise it.

    ``envelope`` is typed ``Any`` rather than ``type`` on purpose: an array-returning
    endpoint declares ``decoder(list[Row])``, and ``list[Row]`` is not a
    ``type``. Annotating it ``type`` would be a lie pyright cannot catch at the call
    site but which is wrong on roughly a third of endpoints. The fidelity walker
    accepts generic decode targets for the same reason.

    Two envelopes are markers rather than decode targets, and a recording keeps
    the body of either as-is rather than decoding it:

    * ``envelope=bytes`` marks an endpoint the client reads with ``as_bytes``: a
      file-shaped body with no schema to decode against. ``bytes`` IS a valid msgspec
      target — it decodes a base64 JSON string — but a raw captured body is not such a
      string, so there is no schema to check it against.
    * ``envelope=type(None)`` marks a VOID WRITE, a method declaring ``expect=nothing``
      and returning ``None`` (a cancel, a delete, a reset). The client reads no body, so
      there is none to check; ``None`` from a client means the call completed.

    ``kw_only=True`` lets ``args`` and ``kwargs`` default to empty (most endpoints need neither) while the
    declaration still reads in order. ``frozen`` freezes the binding, not the ``dict`` behind ``kwargs``.

    ``paginated=True`` marks a walk (a method returning headgate's ``Paginated``): a recording consumes its FIRST
    page only, so the cassette holds one request (:func:`headgate_verify.testing.recording.drive`).

    ``capture=False`` marks an endpoint a recording must never DRIVE (one that places an order, sends a message,
    deletes a record), while leaving it in the table so the exhaustiveness check still sees it. Dropping such an
    endpoint from the table instead would satisfy the recording by defeating the check: a new mutating endpoint would
    then be silently absent rather than reported.

    ``strict=False`` mirrors a client that decodes this endpoint LENIENTLY (``decoder(envelope, strict=False)``, for
    a wire that quotes its numbers). A test decoding the recorded body through a strict decoder would otherwise
    reject the client's own valid payload. It is declared here, not inferred from the client, so a client that
    silently switches to a lax decode does not silently relax its tests with it.

    ``fixture`` names the recorded file when it is not ``<method>.json`` (:attr:`fixture_name`).
    """

    method: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    path: str
    envelope: Any
    fixture: str = ""
    paginated: bool = False
    capture: bool = True
    strict: bool = True

    @property
    def fixture_name(self) -> str:
        """The capture filename — ``fixture`` when given, else ``<method>.json``."""
        return self.fixture or f"{self.method}.json"


def _public_callables(cls: type) -> set[str]:
    """Public callable attribute names on *cls*, including inherited ones.

    ``inspect.getmembers`` reads the CLASS, so a ``@property`` yields the descriptor
    object rather than its value — and a ``property`` is not callable, so it is
    excluded here exactly as it should be.
    """
    return {name for name, _ in inspect.getmembers(cls, callable) if not name.startswith("_")}


def own_endpoint_methods(client_cls: type, *, include_walks: bool = True) -> set[str]:
    """Public methods *client_cls* declares beyond the shared transport surface.

    The exclusion set is derived from :class:`AsyncBaseClient` at runtime rather than
    hardcoded (``aclose``, ``get``, ``post``, ...): a copied list would mean that the day a verb is added to the base
    class, every client's exhaustiveness test starts demanding a manifest entry for it.

    The subtraction is by NAME, so a client that declares its own endpoint named after
    a base verb is silently excluded, the forward check's one blind spot.

    A walk (:func:`own_walk_methods`) is an endpoint unless *include_walks* is false: a walk is often the only reader
    of its path (``get_filings`` returning ``Paginated``), and then it is the wire to record. Pass
    ``include_walks=False`` when every walk sits beside a single-page method reading the same path (the ``walk_``
    beside a ``get_``), so the page method is the one listed and recorded.
    """
    own = _public_callables(client_cls) - _public_callables(AsyncBaseClient)
    return own if include_walks else own - own_walk_methods(client_cls)


def own_walk_methods(client_cls: type) -> set[str]:
    """Public methods of *client_cls* that return headgate's lazy ``Paginated``: its walks.

    A walk is ``return self.paginate(...)``, a sync method returning a lazy iterator, so a recording consumes one page
    of it rather than awaiting it. It is told apart by its return annotation, which the type checkers hold to the
    ``paginate`` call it returns; the ``walk_`` prefix is optional, and a sync method is not enough (a ``stream_``
    method is sync too).
    """
    own = _public_callables(client_cls) - _public_callables(AsyncBaseClient)
    return {name for name in own if _returns_paginated(getattr(client_cls, name))}


def _returns_paginated(method: Callable[..., object]) -> bool:
    """Whether *method* is annotated to return ``Paginated[...]``, read as source text.

    STRING format, because ``Paginated`` is usually a ``TYPE_CHECKING``-only import and evaluating the
    annotation (PEP 649) would raise ``NameError``.
    """
    annotation = inspect.signature(method, annotation_format=Format.STRING).return_annotation
    return str(annotation).startswith(("Paginated[", "headgate.Paginated["))


def uncovered_methods(client_cls: type, manifest: Iterable[Endpoint], *, include_walks: bool = True) -> set[str]:
    """Endpoint methods on *client_cls* that *manifest* does not list.

    This is the exhaustiveness gate: a newly added endpoint is reported until someone
    writes its manifest entry. It checks ONE direction — see :func:`unlisted_methods`
    for the mirror, and :func:`manifest_drift` for the pair as one assertion. *include_walks* is
    :func:`own_endpoint_methods`'.
    """
    return own_endpoint_methods(client_cls, include_walks=include_walks) - {endpoint.method for endpoint in manifest}


def unlisted_methods(client_cls: type, manifest: Iterable[Endpoint]) -> set[str]:
    """Manifest entries naming a method *client_cls* does not have.

    The mirror of :func:`uncovered_methods`, which is structurally blind here: a
    renamed or deleted endpoint leaves a stale entry the forward check passes right
    over, and the entry then degrades into a recording that can never be made.

    Compared against every public callable, not just :func:`own_endpoint_methods`, so
    that an entry naming an inherited verb reads as "not an endpoint" rather than as
    a method that does not exist.
    """
    return {endpoint.method for endpoint in manifest} - _public_callables(client_cls)


def manifest_drift(client_cls: type, manifest: Iterable[Endpoint], *, include_walks: bool = True) -> str:
    """Both directions as one report — empty string when the manifest matches.

    The two checks are one idea, so a suite reports them together::

        if report := manifest_drift(LdaClient, MANIFEST):
            pytest.fail(report)

    Use ``pytest.fail``, NOT ``assert not manifest_drift(...)``: pytest's saferepr
    collapses the newlines and elides the middle of a long string, and the stale
    method names land inside the elided span — so the assert form hides the very
    finding it exists to report.

    Each half names the remedy, because a bare list of method names sends the reader
    hunting for what the failure even means. *include_walks* is :func:`own_endpoint_methods`'.
    """
    manifest = list(manifest)
    problems: list[str] = []
    if missing := uncovered_methods(client_cls, manifest, include_walks=include_walks):
        problems.append(
            f"{client_cls.__name__}: {len(missing)} endpoint(s) have no manifest entry:\n  - "
            + "\n  - ".join(sorted(missing))
            + "\nAdd an Endpoint(...) for each, or — if it is not an endpoint — check "
            "whether it should be private."
        )
    if stale := unlisted_methods(client_cls, manifest):
        problems.append(
            f"{client_cls.__name__}: {len(stale)} manifest entry/entries name a method the "
            f"client does not have:\n  - "
            + "\n  - ".join(sorted(stale))
            + "\nIf the endpoint was RENAMED, update the entry's method= to the new name; "
            "if it was REMOVED, delete the entry and its captured fixture."
        )
    return "\n".join(problems)
