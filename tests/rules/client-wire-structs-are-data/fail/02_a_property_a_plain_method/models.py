class Quote(msgspec.Struct):
    def spread(self) -> float:
        return self.ask - self.bid
