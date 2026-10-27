class Quote(BaseModel, frozen=True):
    """A quote."""

    bid: float
    ask: float | None = None
