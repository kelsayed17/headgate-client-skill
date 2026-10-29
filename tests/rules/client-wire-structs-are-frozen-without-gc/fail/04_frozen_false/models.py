class Quote(msgspec.Struct, frozen=False, gc=False):
    bid: float
