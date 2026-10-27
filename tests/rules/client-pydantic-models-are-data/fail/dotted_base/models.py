import pydantic


class Quote(pydantic.BaseModel):
    bid: float

    def mid(self) -> float:
        return self.bid
