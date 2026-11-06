# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Test helpers for a headgate client's own suite: one way to test any client, the worked examples included.

Each helper is its own module, imported by name, so a suite pulls in only what it uses and importing
``headgate_verify`` (the checker) never needs these dependencies:

* :mod:`~headgate_verify.testing.fidelity`: what a recorded body sends that no msgspec struct declares, what a struct
  declares that no body fills, and the dated baseline of what a package knowingly leaves out;
* :mod:`~headgate_verify.testing.manifest`: the endpoint table a client's tests and recordings read, and the check that
  it lists every endpoint the client has;
* :mod:`~headgate_verify.testing.cassettes`: the response bodies a vcrpy cassette recorded;
* :mod:`~headgate_verify.testing.recording`: recording a live wire into scrubbed cassettes and replaying it offline;
* :mod:`~headgate_verify.testing.creds`: credentials from an operator-named provider, never from this code;
* :mod:`~headgate_verify.testing.plugin`: the pytest options that name that provider;
* :mod:`~headgate_verify.testing.leaf_mock`: a scripted transport spliced at the leaf of a client that takes no
  ``transport=`` (curl), for what :class:`headgate.testing.FakeTransport` cannot reach.

``pip install 'headgate-verify[testing]'`` brings what all but ``recording`` need (headgate with msgspec, pytest);
``[recording]`` adds vcrpy and pytest-recording.
"""
