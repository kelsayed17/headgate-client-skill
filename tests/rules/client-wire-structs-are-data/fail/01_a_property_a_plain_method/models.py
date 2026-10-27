class Quote(msgspec.Struct, frozen=True):
    bid: float
    ask: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
