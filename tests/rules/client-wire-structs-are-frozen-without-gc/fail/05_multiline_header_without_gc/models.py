class Quote(
    msgspec.Struct,
    frozen=True,
    rename="camel",
):
    bid_price: float
