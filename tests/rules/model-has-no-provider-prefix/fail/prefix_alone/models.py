import msgspec


class Pkg(msgspec.Struct, frozen=True):
    id: str
