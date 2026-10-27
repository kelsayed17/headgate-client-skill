# Copyright (c) 2026 Khaled Elsayed
# SPDX-License-Identifier: MIT

"""Verifier configuration."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Settings that tune the checks; fields arrive with the config loader."""
