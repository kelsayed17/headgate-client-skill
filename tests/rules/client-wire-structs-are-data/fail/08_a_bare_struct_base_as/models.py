class Quote(Base, msgspec.Struct, kw_only=True):
    def mid(self) -> float:
        return self.bid
