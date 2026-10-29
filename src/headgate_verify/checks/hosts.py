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
  attribute or any expression is reported), or a conditional of two such names, ``LIVE if live else PAPER``: one
  class on the two hosts of one API (live and paper, production and sandbox) chosen by a flag. Both arms must be
  distinct module-level names on distinct hosts; a third arm (a nested conditional) or a literal arm is reported;
* a client class whose base URL name (either arm's, for a conditional) another client class of the package also
  passes, or whose base URL host another class's base URL also names (hosts compare case-insensitively, ports ignored);
* a string that holds an absolute ``http(s)://`` URL whose host differs from the class's base URL host, passed as the
  URL (first argument or ``url=``) of ``self.get``/``post``/``put``/``patch``/``delete``/``head``/``stream``/
  ``paginate`` in that class (for a conditional base URL, a host that is neither arm's): a literal
  (plain, f- or t-string), a module-level constant of the class's module (or one it imports from a sibling module,
  read there), or a class attribute read as ``self.<name>`` or ``<Class>.<name>``.
  When the class's base URL host cannot be read (no module-level string holds it), every such absolute URL is
  reported, since it cannot be shown to stay on the host.

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

from headgate_verify.finding import Rule
from headgate_verify.syntax import (
    arguments,
    assignments,
    bases,
    classes,
    imported_names,
    keyword_argument,
    line,
    string_body,
)

if TYPE_CHECKING:
    from pathlib import Path

    from ast_grep_py import SgNode, SgRoot

    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RULE = Rule(
    id="one-class-per-host",
    severity="error",
    fix="Give each host its own class, subclassing only AsyncBaseClient and passing `base_url=` a module-level name "
    "of its module; move a call to another host into that host's class.",
)
_BASE = "AsyncBaseClient"
_VERBS = frozenset({"get", "post", "put", "patch", "delete", "head", "stream", "paginate"})
_CONDITIONAL_ARMS = 2
_CONDITIONAL_PARTS = 3
"""A conditional expression's named children: the value if true, the condition and the value if false."""
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
        return line(self.node)

    def finding(self, message: str, at: SgNode | None = None) -> Finding:
        """Return a finding in this class's module, at ``at`` or else at the class's own line."""
        return RULE.finding(self.path, self.line if at is None else line(at), message)


def _host(url: str) -> str | None:
    """Return the lowercase host of an absolute ``http(s)`` URL, or None for anything else."""
    if not _ABSOLUTE.match(url):
        return None
    try:
        host = urlsplit(url).hostname
    except ValueError:
        return url
    return host or url


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
        for original, alias in imported_names(statement):
            bound[alias] = _Import(source, original)
    return bound


def _module_names(root: SgRoot) -> set[str]:
    """Return every name bound at module level by an assignment or an import."""
    names = set(assignments(root.root())) | set(_imports(root))
    for statement in root.root().children():
        if statement.kind() == "import_statement":
            names.update(bound.split(".", 1)[0] for _, bound in imported_names(statement))
    return names


def _client_classes(modules: Modules) -> list[_Class]:
    """Return every class whose bases name ``AsyncBaseClient`` or, transitively, another such class of the package."""
    found = [(path, node, name, tuple(bases(node))) for path, node, name in classes(modules)]
    names = {_BASE}
    clients: dict[int, _Class] = {}
    changed = True
    while changed:
        changed = False
        for index, (path, node, name, node_bases) in enumerate(found):
            if index not in clients and any(base.text() in names for base in node_bases):
                clients[index] = _Class(path, modules[path], node, name, node_bases)
                names.add(name)
                changed = True
    return list(clients.values())


def _base_url(cls: _Class) -> SgNode | None:
    """Return the ``base_url=`` value of the class's ``super().__init__(...)`` call, or None."""
    for call in cls.node.find_all(pattern="super().__init__($$$)"):
        value = keyword_argument(call, "base_url")
        if value is not None:
            return value
    return None


def _constant_text(name: str, root: SgRoot, modules: Modules) -> str | None:
    """Return the module-level string ``name`` of ``root`` holds, following one sibling-module import."""
    value = assignments(root.root()).get(name)
    if value is not None:
        return string_body(value)
    imported = _imports(root).get(name)
    if imported is None:
        return None
    stem = imported.module.rsplit(".", 1)[-1]
    for path, sibling in modules.items():
        if path.stem == stem:
            value = assignments(sibling.root()).get(imported.name)
            return None if value is None else string_body(value)
    return None


@dataclass(frozen=True)
class _Base:
    """A class's base URL: the module-level name of each arm (one, or two for a conditional) and its host."""

    cls: _Class
    names: tuple[str, ...]
    hosts: tuple[str | None, ...]

    @property
    def name(self) -> str:
        return " or ".join(self.names)

    @property
    def host(self) -> str | None:
        """The host when the base URL has one arm whose host is read, else None."""
        return self.hosts[0] if len(self.hosts) == 1 else None


def _read_base(cls: _Class, modules: Modules) -> _Base | Finding:
    """Return the class's base URL name and host, or the finding for a base URL that is missing or not a name."""
    value = _base_url(cls)
    if value is None:
        return cls.finding(f"class {cls.name} passes no base_url= to super().__init__")
    arms = _arms(value)
    if arms is None or any(arm.kind() != "identifier" or arm.text() not in _module_names(cls.root) for arm in arms):
        return cls.finding(
            f"class {cls.name} passes base_url={value.text()}, which is not a module-level name or a conditional of "
            "two (`LIVE if live else PAPER`); name each host once at module level and pass that name",
            at=value,
        )
    names = tuple(arm.text() for arm in arms)
    hosts = tuple(
        _host(text) if (text := _constant_text(name, cls.root, modules)) is not None else None for name in names
    )
    if len(names) == _CONDITIONAL_ARMS:
        if names[0] == names[1]:
            return cls.finding(
                f"class {cls.name} names {names[0]} in both arms of its base_url; use the name alone", at=value
            )
        if hosts[0] is not None and hosts[0] == hosts[1]:
            return cls.finding(
                f"class {cls.name} calls one host in both arms of its base_url ({hosts[0]}); a conditional base URL "
                "chooses between two hosts",
                at=value,
            )
    return _Base(cls, names, hosts)


def _arms(value: SgNode) -> list[SgNode] | None:
    """Return the arms of a base URL: the node itself, or the two outer arms of ``A if cond else B``, else None."""
    if value.kind() != "conditional_expression":
        return [value]
    parts = [part for part in value.named_children() if part.kind() != "comment"]
    return [parts[0], parts[2]] if len(parts) == _CONDITIONAL_PARTS else None


def _chained(clients: list[_Class]) -> set[str]:
    """Return the names of the classes in a client inheritance chain: each subclass of a client class, and its base."""
    client_names = {cls.name for cls in clients}
    return {
        name for cls in clients for base in cls.bases if base.text() in client_names for name in (cls.name, base.text())
    }


def _check_bases(clients: list[_Class]) -> list[Finding]:
    """Report shared client bases and helper bases."""
    client_names = {cls.name for cls in clients}
    findings: list[Finding] = []
    for cls in clients:
        for base in cls.bases:
            if base.text() in client_names:
                findings.append(
                    cls.finding(
                        f"class {cls.name} subclasses the client class {base.text()}; give each host its own class "
                        f"on {_BASE} and share helpers as module-level values"
                    )
                )
            elif base.text() != _BASE:
                findings.append(
                    cls.finding(
                        f"class {cls.name} has a base besides {_BASE}: {base.text()}; a client class subclasses "
                        f"{_BASE} alone"
                    )
                )
    return findings


def _check_distinct(bases: list[_Base]) -> list[Finding]:
    """Report each class whose base URL name, or host, another class's base URL already has."""
    by_name: dict[str, _Base] = {}
    by_host: dict[str, _Base] = {}
    findings: list[Finding] = []
    for base in bases:
        cls = base.cls
        taken = next(((name, by_name[name]) for name in base.names if name in by_name), None)
        if taken is not None:
            name, first = taken
            findings.append(
                cls.finding(
                    f"class {cls.name} shares its base URL name {name} with class {first.cls.name}; one class per host"
                )
            )
            continue
        by_name.update(dict.fromkeys(base.names, base))
        clash = next(((host, by_host[host]) for host in base.hosts if host is not None and host in by_host), None)
        if clash is not None:
            host, first = clash
            findings.append(
                cls.finding(f"class {cls.name} calls host {host}, as class {first.cls.name} does; one class per host")
            )
            continue
        by_host.update({host: base for host in base.hosts if host is not None})
    return findings


def _url_argument(call: SgNode) -> SgNode | None:
    """Return the URL a verb call passes: its ``url=`` argument, else its first positional argument."""
    url = keyword_argument(call, "url")
    if url is not None:
        return url
    positional, _ = arguments(call)
    return positional[0] if positional else None


def _url_text(argument: SgNode, cls: _Class, modules: Modules) -> str | None:
    """Return the string a verb's URL argument holds when it is a literal, a module constant or a class attribute."""
    literal = string_body(argument)
    if literal is not None:
        return literal
    if argument.kind() == "identifier":
        return _constant_text(argument.text(), cls.root, modules)
    value: SgNode | None = None
    if argument.kind() == "attribute":
        owner, attribute = argument.field("object"), argument.field("attribute")
        body = cls.node.field("body")
        if owner is not None and attribute is not None and body is not None and owner.text() in {"self", cls.name}:
            value = assignments(body).get(attribute.text())
    return None if value is None else string_body(value)


def _check_verbs(cls: _Class, base: _Base | None, modules: Modules) -> list[Finding]:
    """Report each absolute URL the class passes a verb on a host other than its base URL's."""
    hosts = () if base is None else base.hosts
    readable = bool(hosts) and None not in hosts
    base_name = None if base is None or not readable else base.name
    findings: list[Finding] = []
    for call in cls.node.find_all(pattern="self.$VERB($$$)"):
        verb = call.get_match("VERB")
        if verb is None or verb.text() not in _VERBS:
            continue
        argument = _url_argument(call)
        text = None if argument is None else _url_text(argument, cls, modules)
        url_host = None if text is None else _host(text)
        if url_host is None or (readable and url_host in hosts):
            continue
        where = (
            f"but its base URL {base_name} is on host{'s' if len(hosts) > 1 else ''} {' or '.join(map(str, hosts))}"
            if base_name is not None
            else "but its base URL host cannot be read, so the URL cannot be shown to stay on it"
        )
        findings.append(
            cls.finding(
                f"class {cls.name} passes an absolute URL on host {url_host} to self.{verb.text()}, {where}; another "
                "host gets its own class",
                at=call,
            )
        )
    return findings


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return the ``one-class-per-host`` findings of ``pkg``."""
    del pkg, config
    clients = _client_classes(modules)
    chained = _chained(clients)
    findings = _check_bases(clients)
    read: list[_Base] = []
    for cls in clients:
        base = None if cls.name in chained else _read_base(cls, modules)
        if isinstance(base, _Base):
            read.append(base)
        elif base is not None:
            findings.append(base)
            base = None
        findings += _check_verbs(cls, base, modules)
    return findings + _check_distinct(read)
