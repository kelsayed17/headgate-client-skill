# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Reading a client's endpoints statically: the verb and path each public method of ``client.py`` sends.

The client is read with ast-grep-py and never imported. A method whose path cannot be read is listed by name
(``unreadable_methods``), never dropped in silence.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_grep_py import SgRoot

from headgate_verify.parsing import LANGUAGE
from headgate_verify.snapshot import Endpoint
from headgate_verify.syntax import arguments, assignments, string_prefix

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from ast_grep_py import SgNode

GET = "GET"
"""The verb of a read."""
_VERBS = {"get": "GET", "post": "POST", "put": "PUT", "patch": "PATCH", "delete": "DELETE", "head": "HEAD"}
_REQUESTS = frozenset({*_VERBS, "paginate", "stream"})


@dataclass(frozen=True)
class _Module:
    """The parts of ``client.py`` the endpoint reader resolves names against."""

    constants: dict[str, SgNode]
    functions: dict[str, SgNode]


def _functions(block: SgNode) -> dict[str, SgNode]:
    """Return ``name -> function definition`` for each function directly in ``block``, decorated or not."""
    functions: dict[str, SgNode] = {}
    for statement in block.named_children():
        node = statement.field("definition") if statement.kind() == "decorated_definition" else statement
        if node is not None and node.kind() == "function_definition" and (name := node.field("name")) is not None:
            functions[name.text()] = node
    return functions


def _module(root: SgNode) -> _Module:
    constants = {name: value for name, value in assignments(root).items() if value.kind() == "string"}
    return _Module(constants, _functions(root))


def _string(node: SgNode, env: Mapping[str, SgNode], module: _Module) -> str | None:
    """Return the text of a plain or t-string literal, each hole inlined when it names a string, else ``{name}``."""
    prefix = string_prefix(node)
    if prefix is None or any(letter in prefix for letter in "fb"):
        return None
    parts: list[str] = []
    for child in node.children()[1:-1]:
        if child.kind() != "interpolation":
            parts.append(child.text())
            continue
        expression = child.named_children()[0]
        inlined = _path(expression, env, module) if expression.kind() == "identifier" else None
        parts.append(f"{{{expression.text()}}}" if inlined is None else inlined)
    return "".join(parts)


def _path(node: SgNode, env: Mapping[str, SgNode], module: _Module) -> str | None:
    """Return the path ``node`` spells: a string, or a name bound in ``env`` or to a module-level string."""
    if node.kind() == "string":
        return _string(node, env, module)
    if node.kind() == "identifier":
        bound = env.get(node.text())
        if bound is not None:
            return _path(bound, {}, module)
        constant = module.constants.get(node.text())
        if constant is not None:
            return _string(constant, {}, module)
    return None


def _parameters(function: SgNode) -> list[str]:
    parameters = function.field("parameters")
    names: list[str] = []
    for parameter in [] if parameters is None else parameters.named_children():
        if parameter.kind() == "identifier":
            names.append(parameter.text())
        elif parameter.kind() == "typed_parameter" and (name := parameter.child(0)) is not None:
            names.append(name.text())
        elif parameter.kind() in {"default_parameter", "typed_default_parameter"}:
            name = parameter.field("name")
            if name is not None:
                names.append(name.text())
    return names


@dataclass(frozen=True)
class Request:
    """A method's request: its endpoint, None when the path cannot be read, and the call that sends it."""

    endpoint: Endpoint | None
    call: str


def _request_name(call: SgNode, receiver: str) -> str | None:
    """Return ``get``, ``paginate``, … when ``call`` is ``<receiver>.<that>(…)``, else None."""
    function = call.field("function")
    if function is None or function.kind() != "attribute":
        return None
    target, attribute = function.field("object"), function.field("attribute")
    if target is None or attribute is None or target.text() != receiver or attribute.text() not in _REQUESTS:
        return None
    return attribute.text()


def _read_request(call: SgNode, name: str, env: Mapping[str, SgNode], module: _Module) -> Endpoint | None:
    positional, keywords = arguments(call)
    route = keywords.get("url", positional[0] if positional else None)
    if name == "stream":
        method = keywords.get("method")
        verb = GET if method is None else _path(method, env, module)
    else:
        verb = _VERBS.get(name, GET)
    path = None if route is None else _path(route, env, module)
    return None if verb is None or path is None else Endpoint(verb.upper(), path)


def _first_request(body: SgNode, receiver: str, env: Mapping[str, SgNode], module: _Module) -> Request | None:
    """Return the first ``<receiver>.<verb>(…)`` call in ``body``, read or not, or None when there is none."""
    for call in body.find_all(kind="call"):
        name = _request_name(call, receiver)
        if name is not None:
            return Request(_read_request(call, name, env, module), f"{receiver}.{name}")
    return None


def _leg(call: SgNode, methods: Mapping[str, SgNode], module: _Module) -> tuple[SgNode, list[str], str] | None:
    """Return ``(leg, parameter names the caller's arguments bind, receiver)`` when ``call`` delegates to a leg."""
    function = call.field("function")
    if function is None:
        return None
    if function.kind() == "attribute" and (target := function.field("object")) is not None and target.text() == "self":
        attribute = function.field("attribute")
        leg = None if attribute is None else methods.get(attribute.text())
        return None if leg is None else (leg, _parameters(leg)[1:], "self")
    if function.kind() == "identifier" and (leg := module.functions.get(function.text())) is not None:
        names = _parameters(leg)
        return None if not names else (leg, names, names[0])
    return None


def _delegated(body: SgNode, methods: Mapping[str, SgNode], module: _Module) -> Request | None:
    """Return the request of the first call in ``body`` to a sibling method or module function that sends one."""
    for call in body.find_all(kind="call"):
        found = _leg(call, methods, module)
        leg_body = None if found is None else found[0].field("body")
        if found is None or leg_body is None:
            continue
        _, names, receiver = found
        positional, keywords = arguments(call)
        env = dict(zip(names, positional, strict=False)) | {k: v for k, v in keywords.items() if k in names}
        request = _first_request(leg_body, receiver, env, module)
        callee = call.field("function")
        if request is not None and callee is not None:
            return Request(request.endpoint, f"{request.call} (through {callee.text()})")
    return None


def read_requests(client_module: Path) -> dict[str, Request]:
    """Return the request of each public method of each class in ``client_module`` that sends one, read or not."""
    root = SgRoot(client_module.read_text(encoding="utf-8"), LANGUAGE).root()
    module = _module(root)
    requests: dict[str, Request] = {}
    for cls in root.find_all(kind="class_definition"):
        class_body = cls.field("body")
        methods = {} if class_body is None else _functions(class_body)
        for name, method in methods.items():
            body = method.field("body")
            if name.startswith("_") or body is None:
                continue
            request = _first_request(body, "self", {}, module) or _delegated(body, methods, module)
            if request is not None:
                requests[name] = request
    return requests


def client_endpoints(client_module: Path) -> dict[str, Endpoint]:
    """Return the verb and path of each public method of each class in ``client_module``, read statically.

    A method's request is its first ``self.<verb>(path, …)`` call (``get``, ``post``, ``put``, ``patch``,
    ``delete``, ``head``; ``paginate`` is GET; ``stream`` is its literal ``method=``, GET by default). The path is a
    string or t-string literal, or a name bound to a module-level one; a t-string hole naming a module-level string
    is inlined, and any other hole becomes ``{expression}`` without its conversion or format spec. A method with no
    such call that delegates to a sibling method or a module-level function sending one is resolved one level: the
    leg's call is read with the leg's parameters bound to the caller's arguments. A method whose path is anything else
    (a parameter of the public method, a call, an f-string, a concatenation) is left out here and listed by
    ``unreadable_methods``; a method that sends no request, even two levels down, is in neither.
    """
    return {name: request.endpoint for name, request in read_requests(client_module).items() if request.endpoint}


def unreadable_methods(client_module: Path) -> dict[str, str]:
    """Return each public method that sends a request whose path cannot be read, with the call that sends it.

    The call is ``self.get``, or ``self.get (through self._leg)`` for a one-level delegate.
    """
    return {name: request.call for name, request in read_requests(client_module).items() if request.endpoint is None}
