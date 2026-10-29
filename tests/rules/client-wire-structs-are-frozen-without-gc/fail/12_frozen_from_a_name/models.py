class Quote(msgspec.Struct, frozen=FROZEN, gc=False):
    bid: float
