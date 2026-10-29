class Quote(
    msgspec.Struct,
    frozen=True,
    gc=False,
    kw_only=True,
    rename="camel",
):
    bid_price: float
