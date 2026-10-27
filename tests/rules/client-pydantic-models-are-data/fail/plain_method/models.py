class Quote(BaseModel, frozen=True):
    bid: float
    ask: float

    def spread(self) -> float:
        return self.ask - self.bid
