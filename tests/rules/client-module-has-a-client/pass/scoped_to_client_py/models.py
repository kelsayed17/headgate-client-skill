"""A module beside client.py; the rule reads only client.py, so no client class is needed here."""

import msgspec


class Item(msgspec.Struct, frozen=True):
    """One item."""

    name: str
