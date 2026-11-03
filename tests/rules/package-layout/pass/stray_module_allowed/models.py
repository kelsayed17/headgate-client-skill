import msgspec


class Item(msgspec.Struct, frozen=True):
    id: str
