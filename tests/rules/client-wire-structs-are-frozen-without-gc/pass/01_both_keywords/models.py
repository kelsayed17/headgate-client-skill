class Quote(msgspec.Struct, frozen=True, gc=False):
    bid: float
