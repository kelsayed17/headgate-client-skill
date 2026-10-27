# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Two warnings, for what a pattern can find but only a reader can judge. A warning never fails the run (exit 0).

``client-except-needs-review``: every ``except`` clause of every module of the package is reported, at the clause's
line, once per clause. A client's errors are ``headgate.errors`` types the caller handles; a handler that turns one
into a return value, or into another exception type, changes what the caller sees. The finding asks the agent to
confirm the handler re-raises a ``headgate.errors`` type, or that the swallowed error is a documented answer, and to
record which with an allow comment carrying the reason. ``try``/``finally`` with no handler is not reported.

``client-cache-with-bearer-auth``: a class (of any module) that passes a cache and also builds an auth that sets an
``Authorization: Bearer`` header is reported once, at the first cache site. A *cache* is a call ``HttpCache(...)`` or
a keyword argument ``cache=`` whose value is not ``None``. A *bearer auth* is a call to ``BearerAuth``, to
``CachedTokenAuth`` or to a class of the package that subclasses either (directly or through other classes of the
package, by bare class name; a subclass whose own ``token_headers`` assignment does not name ``Authorization`` is
not one), or to ``StaticHeaderAuth`` with a dict literal holding an ``Authorization`` key (any case) whose value is
a string starting ``Bearer``. Calls may be spelled bare or as an attribute (``headgate.BearerAuth``).

How serious this is depends on headgate. It never stores ``Authorization`` (nor ``Proxy-Authorization``, ``Cookie``,
a header or query parameter the auth declares, or a URL's userinfo), and under its default
``HttpCache(partition=Partition.CREDENTIAL)`` it keys every entry by an HMAC of the auth's class and
``credential_identity()``, so one credential's responses are never served to another, and it refuses at construction
(``ClientConfigurationError``) an auth that cannot declare its credentials. ``BearerAuth``, ``StaticHeaderAuth`` and
``CachedTokenAuth`` all declare them. The default combination is therefore safe, and the warning is a prompt to
confirm it: that the cache keeps the default partition rather than ``Partition.SHARED`` (which shares entries across
credentials and is only for public data), and that a cached response does not differ by anything the credential does
not capture. A reviewed combination takes an allow comment with the reason.

DISCLOSED: only the class body is read. A cache or an auth built in a module-level constant, a helper function or a
parameter (``auth=make_auth()``, ``policy=POLICY``) is not seen, and an auth class that subclasses
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
        first = next((child for child in arguments.children() if child.is_named()), None) if arguments else None
        if first is not None and first.kind() == "dictionary" and _dict_sets_bearer(first):
            return name
    return None


def _cache_line(cls: SgNode) -> int | None:
    """Return the 1-based line of the first cache site in ``cls``: ``HttpCache(...)`` or ``cache=`` not ``None``."""
    lines = [
        call.range().start.line
        for call in cls.find_all(kind="call")
        if _bare_name(call.field("function")) == "HttpCache"
    ]
    for keyword in cls.find_all(kind="keyword_argument"):
        name, value = keyword.field("name"), keyword.field("value")
        if name is not None and name.text() == "cache" and value is not None and value.text() != "None":
            lines.append(keyword.range().start.line)
    return min(lines) + 1 if lines else None


def check_cache(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return a warning for each class that passes a cache and builds a bearer auth."""
    del config
    bearer = _bearer_classes(modules)
    findings: dict[tuple[Path, int], Finding] = {}
    for path in pkg.modules:
        root = modules.get(path)
        if root is None:
            continue
        for cls in root.root().find_all(kind="class_definition"):
            name = cls.field("name")
            line = _cache_line(cls)
            auth = next(
                (found for call in cls.find_all(kind="call") if (found := _bearer_auth(call, bearer)) is not None),
                None,
            )
            if name is None or line is None or auth is None or (path, line) in findings:
                continue
            findings[path, line] = Finding(
                CACHE_RULE,
                path,
                line,
                f"the client class {name.text()} sets a cache and the bearer auth {auth}; headgate keeps "
                "Authorization out of the cache and partitions entries by credential, so confirm the HttpCache keeps "
                "the default Partition.CREDENTIAL (Partition.SHARED shares entries across credentials) and that no "
                "cached response differs by anything the credential does not capture, or allow this with the reason",
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
