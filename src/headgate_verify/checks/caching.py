# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""A warning, for what a pattern can find but only a reader can judge. A warning never fails the run (exit 0).

``client-cache-with-bearer-auth``: a class (of any module) that builds an ``HttpCache`` whose partition is not shown to
be per credential, and also builds an auth that sets an ``Authorization: Bearer`` header, is reported once, at the
first such ``HttpCache(...)`` call. The cache is judged by its ``partition=`` argument (``HttpCache`` is keyword-only):
absent, or ``Partition.CREDENTIAL`` (spelled bare or as an attribute, ``headgate.Partition.CREDENTIAL``), is the safe
default and is not reported; ``Partition.SHARED`` is reported; anything else (a module constant, a parameter, a call, a
``**options`` unpacking) is reported as a partition the check cannot read. A *bearer auth* is a call to ``BearerAuth``,
to ``CachedTokenAuth`` or to a class of the package that subclasses either (directly or through other classes of the
package, by bare class name; a subclass whose own ``token_headers`` assignment does not name ``Authorization`` is not
one), or to ``StaticHeaderAuth`` with a dict literal (first positional argument or ``headers=``) holding an
``Authorization`` key (any case) whose value is a string starting ``Bearer``. Calls may be spelled bare or as an
attribute (``headgate.BearerAuth``).

Why only a shared or unreadable partition (controller ruling R15): headgate 0.7.0 never stores ``Authorization``
(nor ``Proxy-Authorization``, ``Cookie``, a header or query parameter the auth declares, or a URL's userinfo), and
under the default ``Partition.CREDENTIAL`` keys every entry by an HMAC of the auth's class and
``credential_identity()``, so one credential's responses are never served to another; it also refuses at construction
(``ClientConfigurationError``) an auth that cannot declare its credentials, and ``BearerAuth``, ``StaticHeaderAuth``
and ``CachedTokenAuth`` all declare them. A warning on that default would force an allow comment onto every correct
cached bearer client. ``Partition.SHARED`` shares entries across credentials and is only for public data, so a bearer
client that selects it needs a reason. A reviewed combination takes an allow comment with the reason.

A cache is also found through module-level names: a name used in the class that its module assigns (``CACHE``,
``POLICY = TransportPolicy(cache=CACHE)``) resolves, through up to three assignments, to the ``HttpCache(...)`` calls
it is or is built from, and each is judged by its partition. That finding is reported on the class's use of the name
(so an allow comment goes on that line, or on the enclosing ``def`` or ``class``), not on the module-level
assignment, which may serve several classes.

DISCLOSED: only the class body and its own module's assignments are read. A cache received as a parameter, imported
from another module, or built in a function (``policy=make_policy()``), or an auth built in a helper function
(``auth=make_auth()``), is not seen, and a module-level name rebound or shadowed in the class is still resolved. An
auth class that subclasses ``StaticHeaderAuth`` is not tracked.
"""

import re
from typing import TYPE_CHECKING

from headgate_verify.finding import Rule
from headgate_verify.syntax import assignments, bare_name, bases, classes, derived, line

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode

    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RULE = Rule(
    id="client-cache-with-bearer-auth",
    severity="warning",
    fix="Build the HttpCache on the default `Partition.CREDENTIAL`; keep `Partition.SHARED` only for public data, with "
    "an allow comment saying why.",
)
_BEARER_SEEDS = frozenset({"BearerAuth", "CachedTokenAuth"})
_STATIC_HEADER_AUTH = "StaticHeaderAuth"
_FOLLOW = 3
_UNREADABLE = "a partition it cannot read"
_BEARER_VALUE = re.compile(r"^[rRbBuUfFtT]*(?:'''|\"\"\"|'|\")\s*bearer\b", re.IGNORECASE)
_AUTHORIZATION_KEY = re.compile(r"^[rRbBuUfFtT]*(?:'''|\"\"\"|'|\")authorization(?:'''|\"\"\"|'|\")$", re.IGNORECASE)


def _names_authorization(cls: SgNode) -> bool:
    """Return False when the class assigns ``token_headers`` to something that does not name ``Authorization``."""
    body = cls.field("body")
    headers = None if body is None else assignments(body).get("token_headers")
    return headers is None or "authorization" in headers.text().lower()


def _bearer_classes(modules: Modules) -> set[str]:
    """Return the names of ``BearerAuth``, ``CachedTokenAuth`` and every class of the package deriving from them."""
    hierarchy = [
        (name, {base for node in bases(cls) if (base := bare_name(node)) is not None})
        for _, cls, name in classes(modules)
        if _names_authorization(cls)
    ]
    return derived(set(_BEARER_SEEDS), hierarchy)


def _dict_sets_bearer(node: SgNode) -> bool:
    return any(
        (key := pair.field("key")) is not None
        and (value := pair.field("value")) is not None
        and _AUTHORIZATION_KEY.match(key.text()) is not None
        and _BEARER_VALUE.match(value.text()) is not None
        for pair in node.find_all(kind="pair")
    )


def _headers_argument(call: SgNode) -> SgNode | None:
    """Return the headers a ``StaticHeaderAuth(...)`` call passes: its first argument, else its ``headers=``."""
    argument_list = call.field("arguments")
    for argument in [] if argument_list is None else argument_list.children():
        if argument.kind() == "keyword_argument":
            key = argument.field("name")
            if key is not None and key.text() == "headers":
                return argument.field("value")
        elif argument.is_named() and argument.kind() != "comment":
            return argument
    return None


def _bearer_auth(call: SgNode, bearer: set[str]) -> str | None:
    """Return the class name ``call`` constructs when it is a bearer auth, else None."""
    name = bare_name(call.field("function"))
    if name in bearer:
        return name
    if name == _STATIC_HEADER_AUTH:
        headers = _headers_argument(call)
        if headers is not None and headers.kind() == "dictionary" and _dict_sets_bearer(headers):
            return name
    return None


def _partition_member(node: SgNode | None) -> str | None:
    """Return ``X`` for ``Partition.X`` (bare or as an attribute of a module), or None for any other node."""
    if node is None or node.kind() != "attribute":
        return None
    member, owner = node.field("attribute"), node.field("object")
    if member is None or owner is None:
        return None
    return member.text() if bare_name(owner) == "Partition" else None


def _partition_risk(call: SgNode) -> str | None:
    """Return how an ``HttpCache(...)`` call's partition is not shown to be per credential, or None when it is."""
    argument_list = call.field("arguments")
    for argument in [] if argument_list is None else argument_list.children():
        if argument.kind() in {"dictionary_splat", "list_splat"}:
            return _UNREADABLE
        key = argument.field("name")
        if argument.kind() == "keyword_argument" and key is not None and key.text() == "partition":
            member = _partition_member(argument.field("value"))
            return None if member == "CREDENTIAL" else "Partition.SHARED" if member == "SHARED" else _UNREADABLE
    return None


def _caches_behind(value: SgNode, values: dict[str, SgNode], depth: int) -> list[SgNode]:
    """Return the ``HttpCache(...)`` calls ``value`` is or is built from, following module-level names."""
    calls = [value, *value.find_all(kind="call")] if value.kind() == "call" else []
    found = [call for call in calls if bare_name(call.field("function")) == "HttpCache"]
    if depth:
        names = [value] if value.kind() == "identifier" else value.find_all(kind="identifier")
        for name in names:
            target = values.get(name.text())
            if target is not None and target is not value:
                found += _caches_behind(target, values, depth - 1)
    return found


def _cache_risk(cls: SgNode, values: dict[str, SgNode]) -> tuple[int, str] | None:
    """Return the 1-based line and kind of the first cache in ``cls`` that is not per credential.

    A cache is an ``HttpCache(...)`` call in the class (reported at that call), or one a module-level name used in the
    class resolves to, through up to three assignments (``POLICY = TransportPolicy(cache=CACHE)``,
    ``CACHE = HttpCache(...)``), reported at the class's use of the name.
    """
    risks = [
        (line(call), risk)
        for call in cls.find_all(kind="call")
        if bare_name(call.field("function")) == "HttpCache" and (risk := _partition_risk(call)) is not None
    ]
    for use in cls.find_all(kind="identifier"):
        target = values.get(use.text())
        risks += [
            (line(use), risk)
            for call in (_caches_behind(target, values, _FOLLOW) if target is not None else [])
            if (risk := _partition_risk(call)) is not None
        ]
    return min(risks) if risks else None


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return a warning for each class that builds a bearer auth and a cache not shown to be per credential."""
    del config
    bearer = _bearer_classes(modules)
    findings: dict[tuple[Path, int], Finding] = {}
    for path in pkg.modules:
        root = modules.get(path)
        if root is None:
            continue
        values = assignments(root.root())
        for _, cls, name in classes({path: root}):
            risk = _cache_risk(cls, values)
            auth = next(
                (found for call in cls.find_all(kind="call") if (found := _bearer_auth(call, bearer)) is not None),
                None,
            )
            if risk is None or auth is None or (path, risk[0]) in findings:
                continue
            at, how = risk
            findings[path, at] = RULE.finding(
                path,
                at,
                f"the client class {name} builds the bearer auth {auth} and caches with {how}; Partition.SHARED "
                "shares cached entries across credentials, so use the default Partition.CREDENTIAL, or allow this "
                "with the reason every response is public",
            )
    return list(findings.values())
