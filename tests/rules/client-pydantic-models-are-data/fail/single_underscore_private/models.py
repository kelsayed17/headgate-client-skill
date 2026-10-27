class Quote(BaseModel):
    bid: float

    def _normalised(self) -> float:
        return self.bid
