# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""``model-has-no-provider-prefix``: a model's name does not repeat the provider, which the module path already says.

The provider is the package's directory name; its prefix is that name in PascalCase (``lda`` -> ``Lda``,
``open_meteo`` -> ``OpenMeteo``). Reported: any class in the package's ``models.py``, nested ones included, whose name
starts with the prefix, compared case-insensitively, at a word boundary: the prefix is the whole name, or the next
character is an uppercase letter, a digit or ``_``. So ``LdaFiling``, ``LDAFiling`` and ``Lda`` are reported, while
``Ldap`` (a lowercase letter follows) is not. A name ending ``Params`` or ``Body`` (``WidgetsParams``,
``WidgetsBody``) is a request type the conventions name this way and is not reported (ruling R30). Classes in other
modules (``LdaClient`` in ``client.py``) are not read.

DISCLOSED: an all-capitals name that only begins with the prefix's letters (``SECTION`` in package ``sec``) is
reported; such a class takes an allow comment.
"""

import re
from typing import TYPE_CHECKING

from headgate_verify.finding import Rule
from headgate_verify.syntax import classes, line

if TYPE_CHECKING:
    from headgate_verify.config import Config
    from headgate_verify.finding import Finding
    from headgate_verify.package import Package
    from headgate_verify.parsing import Modules

RULE = Rule(
    id="model-has-no-provider-prefix",
    severity="error",
    fix="Drop the provider name from the class name: `LdaFiling` in package `lda` is `Filing`.",
)
_MODELS = "models.py"
_WORDS = re.compile(r"[^A-Za-z0-9]+")
_REQUEST_SUFFIXES = ("Params", "Body")
"""Request-type names the conventions build from the provider's name (ruling R30); never reported."""


def provider_prefix(package_name: str) -> str:
    """Return ``package_name`` in PascalCase: each ``_``- or ``-``-separated word capitalised, then joined."""
    return "".join(word[:1].upper() + word[1:] for word in _WORDS.split(package_name) if word)


def _prefixed(name: str, prefix: str) -> bool:
    if name.endswith(_REQUEST_SUFFIXES):
        return False
    if not prefix or not name.lower().startswith(prefix.lower()):
        return False
    rest = name[len(prefix) :]
    return not rest or rest[0].isupper() or rest[0].isdigit() or rest[0] == "_"


def check(pkg: Package, modules: Modules, config: Config) -> list[Finding]:
    """Return a finding for each class in ``models.py`` whose name starts with the provider's name."""
    del config
    path = pkg.root / _MODELS
    root = modules.get(path)
    if root is None:
        return []
    prefix = provider_prefix(pkg.root.name)
    return [
        RULE.finding(
            path,
            line(node),
            f"the model class {name} starts with the provider name {prefix}; the module path already says the provider",
        )
        for _, node, name in classes({path: root})
        if _prefixed(name, prefix)
    ]
