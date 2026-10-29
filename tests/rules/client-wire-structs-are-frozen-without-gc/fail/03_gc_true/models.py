class Quote(msgspec.Struct, frozen=True, gc=True):
    bid: float
