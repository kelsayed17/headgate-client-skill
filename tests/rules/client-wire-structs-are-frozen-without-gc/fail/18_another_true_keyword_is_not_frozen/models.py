class Quote(msgspec.Struct, kw_only=True, gc=False):
    bid: float
