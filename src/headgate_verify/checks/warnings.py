# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Two warnings, for what a pattern can find but only a reader can judge. A warning never fails the run (exit 0).

``client-except-needs-review``: every ``except`` clause of every module of the package is reported, at the clause's
line, once per clause. A client's errors are ``headgate.errors`` types the caller handles; a handler that turns one
into a return value, or into another exception type, changes what the caller sees. The finding asks the agent to
confirm the handler re-raises a ``headgate.errors`` type, or that the swallowed error is a documented answer, and to
record which with an allow comment carrying the reason. ``try``/``finally`` with no handler is not reported.

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

DISCLOSED: only the class body is read, and only an ``HttpCache(...)`` call in it. A cache received as a parameter or
built in a module-level constant (``policy=POLICY``), or an auth built in a helper function (``auth=make_auth()``), is
not seen, and an auth class that subclasses
``StaticHeaderAuth`` is not tracked. ``except`` clauses in a module the parser cannot read are not seen (the engine
reports that module as ``parse-error``).
"""

import re
from typing import TYPE_CHECKING

from headgate_verify.finding import Finding

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode, SgRoot

    from headgate_verify.config import Config
    from headgate_verify.package import Package

EXCEPT_RULE = "client-except-needs-review"
CACHE_RULE = "client-cache-with-bearer-auth"
_BEARER_SEEDS = frozenset({"BearerAuth", "CachedTokenAuth"})
_STATIC_HEADER_AUTH = "StaticHeaderAuth"
_UNREADABLE = "a partition it cannot read"
_BEARER_VALUE = re.compile(r"^[rRbBuUfFtT]*(?:'''|\"\"\"|'|\")\s*bearer\b", re.IGNORECASE)
_AUTHORIZATION_KEY = re.compile(r"^[rRbBuUfFtT]*(?:'''|\"\"\"|'|\")authorization(?:'''|\"\"\"|'|\")$", re.IGNORECASE)


def _bare_name(node: SgNode | None) -> str | None:
    """Return the last name of ``Name``, ``a.Name`` or ``Name[...]``, or None for any other node."""
    if node is None:
        return None
    match node.kind():
        case "identifier":
            return node.text()
        case "attribute":
            return _bare_name(node.field("attribute"))
        case "subscript":
            return _bare_name(node.field("value"))
        case _:
            return None


def _bases(cls: SgNode) -> set[str]:
    arguments = cls.field("superclasses")
    if arguments is None:
        return set()
    names = {_bare_name(child) for child in arguments.children() if child.kind() != "keyword_argument"}
    return {name for name in names if name is not None}


def _names_authorization(cls: SgNode) -> bool:
    """Return False when the class assigns ``token_headers`` to something that does not name ``Authorization``."""
    body = cls.field("body")
    for statement in body.children() if body is not None else []:
        for assignment in statement.children():
            left = assignment.field("left") if assignment.kind() == "assignment" else None
            right = assignment.field("right")
            if left is not None and left.text() == "token_headers" and right is not None:
                return "authorization" in right.text().lower()
    return True


def _bearer_classes(modules: dict[Path, SgRoot]) -> set[str]:
    """Return the names of ``BearerAuth``, ``CachedTokenAuth`` and every class of the package deriving from them."""
    classes = [
        (name.text(), _bases(node), node)
        for root in modules.values()
        for node in root.root().find_all(kind="class_definition")
        if (name := node.field("name")) is not None
    ]
    known = set(_BEARER_SEEDS)
    grown = True
    while grown:
        grown = False
        for name, bases, node in classes:
            if name not in known and bases & known and _names_authorization(node):
                known.add(name)
                grown = True
    return known


def _dict_sets_bearer(node: SgNode) -> bool:
    return any(
        (key := pair.field("key")) is not None
        and (value := pair.field("value")) is not None
        and _AUTHORIZATION_KEY.match(key.text()) is not None
        and _BEARER_VALUE.match(value.text()) is not None
        for pair in node.find_all(kind="pair")
    )


def _bearer_auth(call: SgNode, bearer: set[str]) -> str | None:
    """Return the class name ``call`` constructs when it is a bearer auth, else None."""
    name = _bare_name(call.field("function"))
    if name in bearer:
        return name
    if name == _STATIC_HEADER_AUTH:
        arguments = call.field("arguments")
        for argument in arguments.children() if arguments is not None else []:
            if argument.kind() == "keyword_argument":
                key, value = argument.field("name"), argument.field("value")
                headers = value if key is not None and key.text() == "headers" else None
            else:
                headers = argument if argument.is_named() and argument.kind() != "comment" else None
            if headers is not None and headers.kind() == "dictionary" and _dict_sets_bearer(headers):
                return name
            if headers is not None:
                break
    return None


def _partition_risk(call: SgNode) -> str | None:
    """Return how an ``HttpCache(...)`` call's partition is not shown to be per credential, or None when it is."""
    arguments = call.field("arguments")
    for argument in arguments.children() if arguments is not None else []:
        if argument.kind() in {"dictionary_splat", "list_splat"}:
            return _UNREADABLE
        key, value = argument.field("name"), argument.field("value")
        if argument.kind() == "keyword_argument" and key is not None and key.text() == "partition":
            member = _partition_member(value)
            return None if member == "CREDENTIAL" else "Partition.SHARED" if member == "SHARED" else _UNREADABLE
    return None


def _partition_member(node: SgNode | None) -> str | None:
    """Return ``X`` for ``Partition.X`` (bare or as an attribute of a module), or None for any other node."""
    if node is None or node.kind() != "attribute":
        return None
    member, owner = node.field("attribute"), node.field("object")
    if member is None or owner is None:
        return None
    owner_name = _bare_name(owner)
    return member.text() if owner_name == "Partition" else None


def _cache_risk(cls: SgNode) -> tuple[int, str] | None:
    """Return the 1-based line and kind of the first ``HttpCache(...)`` in ``cls`` that is not per credential."""
    risks = [
        (call.range().start.line + 1, risk)
        for call in cls.find_all(kind="call")
        if _bare_name(call.field("function")) == "HttpCache" and (risk := _partition_risk(call)) is not None
    ]
    return min(risks) if risks else None


def check_cache(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return a warning for each class that builds a bearer auth and a cache not shown to be per credential."""
    del config
    bearer = _bearer_classes(modules)
    findings: dict[tuple[Path, int], Finding] = {}
    for path in pkg.modules:
        root = modules.get(path)
        if root is None:
            continue
        for cls in root.root().find_all(kind="class_definition"):
            name = cls.field("name")
            risk = _cache_risk(cls)
            auth = next(
                (found for call in cls.find_all(kind="call") if (found := _bearer_auth(call, bearer)) is not None),
                None,
            )
            if name is None or risk is None or auth is None or (path, risk[0]) in findings:
                continue
            line, how = risk
            findings[path, line] = Finding(
                CACHE_RULE,
                path,
                line,
                f"the client class {name.text()} builds the bearer auth {auth} and caches with {how}; Partition.SHARED "
                "shares cached entries across credentials, so use the default Partition.CREDENTIAL, or allow this "
                "with the reason every response is public",
                "warning",
            )
    return list(findings.values())


def check_except(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return a warning for each ``except`` clause in the package."""
    del config
    return [
        Finding(
            EXCEPT_RULE,
            path,
            clause.range().start.line + 1,
            "this handler must re-raise a headgate.errors type, or the error must be a documented answer of the "
            "provider; confirm which, and record the reason with an allow comment",
            "warning",
        )
        for path in pkg.modules
        if (root := modules.get(path)) is not None
        for clause in root.root().find_all(kind="except_clause")
    ]
