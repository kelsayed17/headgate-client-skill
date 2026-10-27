class Quote(Base, BaseModel, frozen=True):
    bid: float

    def mid(self) -> float:
        return self.bid
