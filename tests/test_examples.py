# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""The worked examples pass the verifier, and a copy of one breaking each anti-goal of the design does not.

Each mutation is applied to a copy of a worked example in a temporary directory, beside a ``pyproject.toml`` declaring
its flavour's headgate extra as the repo's own does, so the unmutated copy passes and every finding comes from the
mutation. The msgspec example (``examples/msgspec/lda``) takes one mutation per anti-goal; the pydantic one
(``examples/pydantic/open_meteo``, two hosts) takes a second for anti-goal 1, a base class its two clients share.
Anti-goals 5 (an error caught and dropped) and 7 (a bearer response cached in a shared partition) are review checks,
so their mutations must yield a warning; the others must yield an error. Anti-goal 3 (a method named after a doc
heading) is the naming test's to catch, not the verifier's (the design: the verifier "does not run the client's tests
or the naming test"), so its mutation is checked with ``check_names``.
"""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pytest

from headgate_verify.engine import verify
from headgate_verify.naming import check_names

if TYPE_CHECKING:
    from headgate_verify.finding import Severity

EXAMPLES = Path(__file__).parent.parent / "examples"


class Example(NamedTuple):
    """A worked example: its directory and its model flavour, the headgate extra its copy's project declares."""

    path: Path
    flavour: str


LDA = Example(EXAMPLES / "msgspec" / "lda", "msgspec")
OPEN_METEO = Example(EXAMPLES / "pydantic" / "open_meteo", "pydantic")


class Edit(NamedTuple):
    """Replace the one occurrence of ``old`` in the package's ``module`` with ``new``."""

    module: str
    old: str
    new: str


class Mutation(NamedTuple):
    """One anti-goal broken in the copy: its edits, and the findings it must yield (every rule in ``rules``)."""

    anti_goal: str
    edits: tuple[Edit, ...]
    severity: Severity
    rules: frozenset[str]
    example: Example = LDA


MUTATIONS = [
    Mutation(
        "1-second-host-in-the-class",
        (
            Edit(
                "client.py",
                '"api/v1/constants/general/states/"',
                '"https://www.senate.gov/api/v1/constants/general/states/"',
            ),
        ),
        "error",
        frozenset({"one-class-per-host"}),
    ),
    Mutation(
        "2-two-endpoints-in-one-method",
        (
            Edit(
                "client.py",
                '''    async def get_constants_lobbyist_prefixes(self) -> list[Constant]:
        """Return the name prefixes a lobbyist may have (``dr``, ``mr``, …)."""
        return await self.get("api/v1/constants/lobbyist/prefixes/", expect=CONSTANTS)

    async def get_constants_lobbyist_suffixes(self) -> list[Constant]:
        """Return the name suffixes a lobbyist may have."""
        return await self.get("api/v1/constants/lobbyist/suffixes/", expect=CONSTANTS)
''',
                '''    async def get_constants_lobbyist(self) -> tuple[list[Constant], list[Constant]]:
        """Return the name prefixes and the name suffixes a lobbyist may have."""
        prefixes = await self.get("api/v1/constants/lobbyist/prefixes/", expect=CONSTANTS)
        suffixes = await self.get("api/v1/constants/lobbyist/suffixes/", expect=CONSTANTS)
        return prefixes, suffixes
''',
            ),
        ),
        "error",
        frozenset({"client-method-shape"}),
    ),
    Mutation(
        "4-none-from-a-bare-try-except",
        (
            Edit(
                "client.py",
                '        return await self.get(t"api/v1/filings/{filing_uuid}/", expect=FILING_OR_NONE)',
                """        try:
            return await self.get(t"api/v1/filings/{filing_uuid}/", expect=FILING)
        except Exception:
            return None""",
            ),
        ),
        "error",
        frozenset({"client-method-shape", "client-method-returns"}),
    ),
    Mutation(
        "5-error-caught-and-dropped",
        (
            Edit(
                "client.py",
                '        return await self.get("api/v1/constants/general/states/", expect=CONSTANTS)',
                """        try:
            return await self.get("api/v1/constants/general/states/", expect=CONSTANTS)
        except UpstreamStatusError:
            return []""",
            ),
        ),
        "warning",
        frozenset({"client-except-needs-review"}),
    ),
    Mutation(
        "6-transport-wrapped",
        (
            Edit(
                "client.py",
                "class LdaClient(AsyncBaseClient):",
                '''class LoggingTransport(httpx2.AsyncBaseTransport):
    """Send each request on the transport handed in."""

    def __init__(self, inner: httpx2.AsyncBaseTransport) -> None:
        """Wrap ``inner``."""
        self._inner = inner

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        """Send ``request`` on the wrapped transport."""
        return await self._inner.handle_async_request(request)


class LdaClient(AsyncBaseClient):''',
            ),
        ),
        "error",
        frozenset({"client-transport-subclassed-not-wrapped"}),
    ),
    Mutation(
        "7-bearer-response-cached-shared",
        (
            Edit(
                "client.py",
                "def __init__(self, *, user_agent: str,",
                "def __init__(self, *, token: str, user_agent: str,",
            ),
            Edit(
                "client.py",
                "            rate=PACE,\n",
                """            rate=PACE,
            auth=BearerAuth(token),
            policy=TransportPolicy(cache=HttpCache(max_entries=256, partition=Partition.SHARED)),
""",
            ),
        ),
        "warning",
        frozenset({"client-cache-with-bearer-auth"}),
    ),
    Mutation(
        "8-model-with-provider-prefix",
        (Edit("models.py", "class Registrant(msgspec.Struct", "class LdaRegistrant(msgspec.Struct"),),
        "error",
        frozenset({"model-has-no-provider-prefix"}),
    ),
    Mutation(
        "1-shared-client-base-class",
        (
            Edit(
                "client.py",
                "class ForecastClient(AsyncBaseClient):",
                '''class WeatherClient(AsyncBaseClient):
    """What the two hosts' clients share."""


class ForecastClient(WeatherClient):''',
            ),
            Edit("client.py", "class ArchiveClient(AsyncBaseClient):", "class ArchiveClient(WeatherClient):"),
        ),
        "error",
        frozenset({"one-class-per-host"}),
        OPEN_METEO,
    ),
]
"""One mutation per anti-goal the verifier checks: 1 (twice), 2, 4, 6 and 8 as errors, 5 and 7 as warnings."""


def copy_example(tmp_path: Path, example: Example, *edits: Edit) -> Path:
    """Return a copy of ``example`` under ``tmp_path``, beside a ``pyproject.toml``, with ``edits`` applied."""
    package = tmp_path / example.path.name
    shutil.copytree(example.path, package, ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "example-copy"\nversion = "0"\ndependencies = ["headgate[{example.flavour}]>=0.8.0"]\n',
        encoding="utf-8",
    )
    for edit in edits:
        module = package / edit.module
        text = module.read_text(encoding="utf-8")
        assert text.count(edit.old) == 1, f"{edit.module} no longer holds the text to mutate: {edit.old!r}"
        module.write_text(text.replace(edit.old, edit.new), encoding="utf-8")
    return package


def test_examples_pass_verifier() -> None:
    """Every worked example passes the verifier with no finding at all, warnings included."""
    assert verify([EXAMPLES]) == []


@pytest.mark.parametrize("example", [LDA, OPEN_METEO], ids=["lda", "open_meteo"])
def test_unmutated_copy_passes_verifier(tmp_path: Path, example: Example) -> None:
    """The copies the mutations start from pass, so each finding below comes from its mutation."""
    package = copy_example(tmp_path, example)

    assert verify([package]) == []
    assert check_names(package / "client.py", package / "docs_paths.json") == []


@pytest.mark.parametrize("mutation", MUTATIONS, ids=[mutation.anti_goal for mutation in MUTATIONS])
def test_each_anti_goal_mutation_fails(tmp_path: Path, mutation: Mutation) -> None:
    """The copy with the anti-goal broken yields a finding of each expected rule, at the expected severity."""
    package = copy_example(tmp_path, mutation.example, *mutation.edits)

    found = {finding.rule for finding in verify([package]) if finding.severity == mutation.severity}

    assert mutation.rules <= found


def test_heading_name_mutation_fails_the_name_check(tmp_path: Path) -> None:
    """Anti-goal 3: a read named after its doc heading (``list_registrants``) fails the naming test, naming the fix."""
    package = copy_example(tmp_path, LDA, Edit("client.py", "def get_registrants(", "def list_registrants("))

    assert check_names(package / "client.py", package / "docs_paths.json") == [
        (
            "list_registrants reads GET api/v1/registrants/ and should be named get_registrants or walk_registrants "
            "(or add an override "
            "with a reason)"
        )
    ]
