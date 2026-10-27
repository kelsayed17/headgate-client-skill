from typing import TypedDict

import msgspec


class WidgetsParams(TypedDict, total=False):
    page: int


class WidgetsBody(msgspec.Struct, frozen=True):
    name: str


class Widget(msgspec.Struct, frozen=True):
    id: str
