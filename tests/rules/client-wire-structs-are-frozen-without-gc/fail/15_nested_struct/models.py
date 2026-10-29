class Outer(msgspec.Struct, frozen=True, gc=False):
    class Nested(msgspec.Struct, frozen=True):
        x: int

    y: int
