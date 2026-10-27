class Quote(msgspec.Struct):
    def _normalised(self) -> float:
        return self.bid
