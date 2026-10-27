class Quote(msgspec.Struct):
    @classmethod
    def empty(cls) -> Quote:
        return cls(bid=0.0, ask=0.0)
