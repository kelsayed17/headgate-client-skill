# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""``one-class-per-host``: each host the package calls has its own client class, and each class calls only its host.

A *client class* is a class in any module of the package whose bases name ``AsyncBaseClient`` by that bare name, or
name another client class of the package (by its bare class name, in any module). Reported:

* a class whose bases name another client class of the package (a shared client base): one finding per subclass,
  and neither class is read for its base URL, since the base URL then lives in the shared class;
* a client class with a base besides ``AsyncBaseClient`` (a shared helper base; keyword arguments such as
  ``metaclass=`` are not bases);
* a client class whose ``super().__init__(...)`` passes no ``base_url=``, or passes something other than a
  module-level name of its module (a name bound by a module-level assignment or import; a literal, a parameter, an
  attribute or any expression is reported);
* a client class whose base URL name another client class of the package also passes, or whose base URL host another
  class's base URL also names (hosts compare case-insensitively, ports ignored);
* a string that holds an absolute ``http(s)://`` URL whose host differs from the class's base URL host, passed as the
  URL (first argument or ``url=``) of ``self.get``/``post``/``put``/``patch``/``delete``/``head``/``stream``/
  ``paginate`` in that class: a literal (plain, f- or t-string), a module-level constant of the class's module, or a
  class attribute read as ``self.<name>`` or ``<Class>.<name>``. When the class's base URL host cannot be read (no
  module-level string holds it), every such absolute URL is reported, since it cannot be shown to stay on the host.

A base URL name imported from a sibling module (``from .hosts import API``) has its host read from that module's
module-level assignment. A URL the API itself returned is followed freely: a pager such as headgate's ``NextUrl``
reads it from the body at run time, and a method may pass a URL parameter to a verb; neither is a literal or a
constant. Not read: a URL built at run time from a constant (``OTHER + "/x"``, ``f"{OTHER}/x"``), which the
``client-paths-*`` rules refuse as a built path, and a local variable assigned a literal inside a method, which
``client-method-shape`` refuses as a second statement.
"""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from headgate_verify.finding import Finding

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode, SgRoot

    from headgate_verify.config import Config
    from headgate_verify.package import Package

RULE = "one-class-per-host"
_BASE = "AsyncBaseClient"
_VERBS = frozenset({"get", "post", "put", "patch", "delete", "head", "stream", "paginate"})
_STRING_PREFIX = re.compile(r"^[rRbBuUfFtT]*('''|\"\"\"|'|\")")
_ABSOLUTE = re.compile(r"^https?://", re.IGNORECASE)


@dataclass(frozen=True)
class _Class:
    path: Path
    root: SgRoot
    node: SgNode
    name: str
    bases: tuple[SgNode, ...]

    @property
    def line(self) -> int:
        return self.node.range().start.line + 1


def _finding(path: Path, line: int, message: str) -> Finding:
    return Finding(RULE, path, line, message, "error")


def _string_text(node: SgNode) -> str | None:
    """Return the text between a string literal's quotes (holes kept as written), or None for any other node."""
    if node.kind() != "string":
        return None
    text = node.text()
    prefix = _STRING_PREFIX.match(text)
    if prefix is None:
        return None
    quote = prefix.group(1)
    return text[prefix.end() : len(text) - len(quote)]


def _host(url: str) -> str | None:
    """Return the lowercase host of an absolute ``http(s)`` URL, or None for anything else."""
    if not _ABSOLUTE.match(url):
        return None
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return url
    return host or url


def _assignments(block: SgNode) -> dict[str, SgNode]:
    """Return ``name -> value`` for each ``name = value`` (or ``name: T = value``) directly in ``block``."""
    values: dict[str, SgNode] = {}
    for statement in block.children():
        if statement.kind() != "expression_statement":
            continue
        for assignment in statement.children():
            if assignment.kind() != "assignment":
                continue
            left, right = assignment.field("left"), assignment.field("right")
            if left is not None and right is not None and left.kind() == "identifier":
                values[left.text()] = right
    return values


@dataclass(frozen=True)
class _Import:
    module: str
    """The dotted module the name comes from, its leading dots removed."""
    name: str


def _imports(root: SgRoot) -> dict[str, _Import]:
    """Return ``bound name -> where it comes from`` for each module-level ``from X import name [as bound]``."""
    bound: dict[str, _Import] = {}
    for statement in root.root().children():
        if statement.kind() != "import_from_statement":
            continue
        module = statement.field("module_name")
        source = module.text().lstrip(".") if module is not None else ""
        for name in statement.field_children("name"):
            original = name.field("name") if name.kind() == "aliased_import" else name
            alias = name.field("alias") if name.kind() == "aliased_import" else name
            if original is not None and alias is not None:
                bound[alias.text()] = _Import(source, original.text())
    return bound


def _module_names(root: SgRoot) -> set[str]:
    """Return every name bound at module level by an assignment or an import."""
    names = set(_assignments(root.root())) | set(_imports(root))
    for statement in root.root().children():
        if statement.kind() == "import_statement":
            for name in statement.field_children("name"):
                bound = name.field("alias") if name.kind() == "aliased_import" else name
                if bound is not None:
                    names.add(bound.text().split(".", 1)[0])
    return names


def _client_classes(modules: dict[Path, SgRoot]) -> list[_Class]:
    """Return every class whose bases name ``AsyncBaseClient`` or, transitively, another such class of the package."""
    classes = [
        _Class(path, root, node, name.text(), tuple(_bases(node)))
        for path, root in modules.items()
        for node in root.root().find_all(kind="class_definition")
        if (name := node.field("name")) is not None
    ]
    names = {_BASE}
    clients: list[_Class] = []
    changed = True
    while changed:
        changed = False
        for cls in classes:
            if cls not in clients and any(base.text() in names for base in cls.bases):
                clients.append(cls)
                names.add(cls.name)
                changed = True
    return clients


def _bases(node: SgNode) -> list[SgNode]:
    superclasses = node.field("superclasses")
    if superclasses is None:
        return []
    return [child for child in superclasses.children() if child.is_named() and child.kind() != "keyword_argument"]


def _base_url(cls: _Class) -> SgNode | None:
    """Return the ``base_url=`` value of the class's ``super().__init__(...)`` call, or None."""
    for call in cls.node.find_all(pattern="super().__init__($$$)"):
        arguments = call.field("arguments")
        if arguments is None:
            continue
        for argument in arguments.children():
            if argument.kind() != "keyword_argument":
                continue
            name, value = argument.field("name"), argument.field("value")
            if name is not None and value is not None and name.text() == "base_url":
                return value
    return None


def _constant_host(name: str, root: SgRoot, modules: dict[Path, SgRoot]) -> str | None:
    """Return the host of the module-level string ``name`` of ``root``, following one sibling-module import."""
    value = _assignments(root.root()).get(name)
    if value is not None:
        text = _string_text(value)
        return None if text is None else _host(text)
    imported = _imports(root).get(name)
    if imported is None:
        return None
    stem = imported.module.rsplit(".", 1)[-1]
    for path, sibling in modules.items():
        if path.stem == stem:
            value = _assignments(sibling.root()).get(imported.name)
            text = None if value is None else _string_text(value)
            return None if text is None else _host(text)
    return None


@dataclass(frozen=True)
class _Base:
    cls: _Class
    name: str
    host: str | None


def _read_base(cls: _Class, modules: dict[Path, SgRoot], findings: list[Finding]) -> _Base | None:
    value = _base_url(cls)
    if value is None:
        findings.append(_finding(cls.path, cls.line, f"class {cls.name} passes no base_url= to super().__init__"))
        return None
    if value.kind() != "identifier" or value.text() not in _module_names(cls.root):
        findings.append(
            _finding(
                cls.path,
                value.range().start.line + 1,
                f"class {cls.name} passes base_url={value.text()}, which is not a module-level name; name each host "
                "once at module level and pass that name",
            )
        )
        return None
    return _Base(cls, value.text(), _constant_host(value.text(), cls.root, modules))


def _check_bases(clients: list[_Class], findings: list[Finding]) -> set[str]:
    """Report shared client bases and helper bases; return the names of classes in a client inheritance chain."""
    client_names = {cls.name for cls in clients}
    chained: set[str] = set()
    for cls in clients:
        for base in cls.bases:
            if base.text() in client_names:
                chained.update({cls.name, base.text()})
                findings.append(
                    _finding(
                        cls.path,
                        cls.line,
                        f"class {cls.name} subclasses the client class {base.text()}; give each host its own class "
                        f"on {_BASE} and share helpers as module-level values",
                    )
                )
            elif base.text() != _BASE:
                findings.append(
                    _finding(
                        cls.path,
                        cls.line,
                        f"class {cls.name} has a base besides {_BASE}: {base.text()}; a client class subclasses "
                        f"{_BASE} alone",
                    )
                )
    return chained


def _check_distinct(bases: list[_Base], findings: list[Finding]) -> None:
    by_name: dict[str, _Base] = {}
    by_host: dict[str, _Base] = {}
    for base in bases:
        cls = base.cls
        first = by_name.setdefault(base.name, base)
        if first is not base:
            findings.append(
                _finding(
                    cls.path,
                    cls.line,
                    f"class {cls.name} shares its base URL name {base.name} with class {first.cls.name}; one class "
                    "per host",
                )
            )
            continue
        if base.host is None:
            continue
        first = by_host.setdefault(base.host, base)
        if first is not base:
            findings.append(
                _finding(
                    cls.path,
                    cls.line,
                    f"class {cls.name} calls host {base.host}, as class {first.cls.name} does; one class per host",
                )
            )


def _url_argument(call: SgNode) -> SgNode | None:
    arguments = call.field("arguments")
    if arguments is None:
        return None
    for argument in arguments.children():
        if argument.kind() == "keyword_argument":
            name = argument.field("name")
            if name is not None and name.text() == "url":
                return argument.field("value")
        elif argument.is_named() and argument.kind() != "comment":
            return argument
    return None


def _url_text(argument: SgNode, cls: _Class) -> str | None:
    """Return the string a verb's URL argument holds when it is a literal, a module constant or a class attribute."""
    literal = _string_text(argument)
    if literal is not None:
        return literal
    value: SgNode | None = None
    if argument.kind() == "identifier":
        value = _assignments(cls.root.root()).get(argument.text())
    elif argument.kind() == "attribute":
        owner, attribute = argument.field("object"), argument.field("attribute")
        body = cls.node.field("body")
        if owner is not None and attribute is not None and body is not None and owner.text() in {"self", cls.name}:
            value = _assignments(body).get(attribute.text())
    return None if value is None else _string_text(value)


def _check_verbs(cls: _Class, host: str | None, base_name: str | None, findings: list[Finding]) -> None:
    for call in cls.node.find_all(pattern="self.$VERB($$$)"):
        verb = call.get_match("VERB")
        if verb is None or verb.text() not in _VERBS:
            continue
        argument = _url_argument(call)
        text = None if argument is None else _url_text(argument, cls)
        url_host = None if text is None else _host(text)
        if url_host is None or url_host == host:
            continue
        where = (
            f"but its base URL {base_name} is on host {host}"
            if host is not None and base_name is not None
            else "but its base URL host cannot be read, so the URL cannot be shown to stay on it"
        )
        findings.append(
            _finding(
                cls.path,
                call.range().start.line + 1,
                f"class {cls.name} passes an absolute URL on host {url_host} to self.{verb.text()}, {where}; another "
                "host gets its own class",
            )
        )


def check(pkg: Package, modules: dict[Path, SgRoot], config: Config) -> list[Finding]:
    """Return the ``one-class-per-host`` findings of ``pkg``."""
    del pkg, config
    findings: list[Finding] = []
    clients = _client_classes(modules)
    chained = _check_bases(clients, findings)
    bases: list[_Base] = []
    for cls in clients:
        base = None if cls.name in chained else _read_base(cls, modules, findings)
        if base is not None:
            bases.append(base)
        _check_verbs(cls, None if base is None else base.host, None if base is None else base.name, findings)
    _check_distinct(bases, findings)
    return findings
