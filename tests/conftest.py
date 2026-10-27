# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Pytest configuration: the fixture packages under ``rules/`` are data, never collected as tests."""

collect_ignore = ["rules"]
