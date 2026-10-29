class Quote(msgspec.Struct, frozen=True, omit_defaults=False):
    bid: float
