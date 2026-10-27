from msgspec import Struct


class Quote(Struct):
    def mid(self) -> float:
        return self.bid
