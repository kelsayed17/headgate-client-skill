import msgspec


class PKGFiling(msgspec.Struct, frozen=True):
    id: str
