import msgspec


class Filing(msgspec.Struct, frozen=True):
    id: str
