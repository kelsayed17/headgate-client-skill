# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Readers of tree-sitter Python trees shared by the checks, the allow comments and the naming helper.

Each reads one construct the way the conventions spell it and returns None (or nothing) for any other shape, so a
caller never guesses at a node it cannot read.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from ast_grep_py import SgNode

    from headgate_verify.parsing import Modules

_SPLATS = frozenset({"list_splat", "dictionary_splat"})


def line(node: SgNode) -> int:
    """Return the 1-based line ``node`` starts on."""
    return node.range().start.line + 1


def statements(block: SgNode) -> list[SgNode]:
    """Return the statements directly in ``block`` (a module or a body), comments left out."""
    return [child for child in block.children() if child.is_named() and child.kind() != "comment"]


def assignments(block: SgNode) -> dict[str, SgNode]:
    """Return ``name -> value`` for each ``name = value`` (or ``name: T = value``) directly in ``block``; last wins."""
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


def bare_name(node: SgNode | None) -> str | None:
    """Return the last name of ``Name``, ``a.Name`` or ``Name[...]``, or None for any other node."""
    if node is None:
        return None
    match node.kind():
        case "identifier":
            return node.text()
        case "attribute":
            return bare_name(node.field("attribute"))
        case "subscript":
            return bare_name(node.field("value"))
        case _:
            return None


def classes(modules: Modules) -> Iterator[tuple[Path, SgNode, str]]:
    """Yield ``(path, class node, class name)`` for every class at any depth of every module, in module order."""
    for path, root in modules.items():
        for node in root.root().find_all(kind="class_definition"):
            name = node.field("name")
            if name is not None:
                yield path, node, name.text()


def bases(cls: SgNode) -> list[SgNode]:
    """Return the base expressions of a class definition; keyword arguments (``metaclass=``) are not bases."""
    superclasses = cls.field("superclasses")
    if superclasses is None:
        return []
    return [child for child in statements(superclasses) if child.kind() != "keyword_argument"]


def derived(seeds: set[str], hierarchy: list[tuple[str, set[str]]]) -> set[str]:
    """Return ``seeds`` and each name of ``hierarchy`` (``(name, base names)``) deriving from one, at any depth."""
    known = set(seeds)
    grown = True
    while grown:
        grown = False
        for name, base_names in hierarchy:
            if name not in known and base_names & known:
                known.add(name)
                grown = True
    return known


def keyword_argument(call: SgNode, name: str) -> SgNode | None:
    """Return the value of the ``name=`` argument of ``call``, or None when it passes none."""
    arguments = call.field("arguments")
    for argument in [] if arguments is None else arguments.children():
        if argument.kind() == "keyword_argument":
            key = argument.field("name")
            if key is not None and key.text() == name:
                return argument.field("value")
    return None


def arguments(call: SgNode) -> tuple[list[SgNode], dict[str, SgNode]]:
    """Return the positional and the keyword arguments of ``call``, ``*``/``**`` unpackings left out."""
    positional: list[SgNode] = []
    keywords: dict[str, SgNode] = {}
    argument_list = call.field("arguments")
    for argument in [] if argument_list is None else statements(argument_list):
        if argument.kind() == "keyword_argument":
            name, value = argument.field("name"), argument.field("value")
            if name is not None and value is not None:
                keywords[name.text()] = value
        elif argument.kind() not in _SPLATS:
            positional.append(argument)
    return positional, keywords


def imported_names(statement: SgNode) -> list[tuple[str, str]]:
    """Return ``(name as written, name bound)`` for each name an ``import`` or ``from … import`` statement imports.

    ``import a.b`` gives ``("a.b", "a.b")``; ``import a.b as c`` and ``from m import b as c`` give ``(…, "c")``.
    """
    found: list[tuple[str, str]] = []
    for name in statement.field_children("name"):
        aliased = name.kind() == "aliased_import"
        original = name.field("name") if aliased else name
        bound = name.field("alias") if aliased else name
        if original is not None and bound is not None:
            found.append((original.text(), bound.text()))
    return found


def string_prefix(node: SgNode) -> str | None:
    """Return the lower-cased prefix letters of a string literal (``f``, ``rb``, ``t``, or ``""``), else None."""
    start = node.child(0) if node.kind() == "string" else None
    return None if start is None else start.text().lower().rstrip("'\"")


def string_body(node: SgNode) -> str | None:
    """Return the text between a string literal's quotes, holes kept as written, or None for any other node."""
    if node.kind() != "string":
        return None
    children, text = node.children(), node.text()
    return text[len(children[0].text()) : len(text) - len(children[-1].text())]
