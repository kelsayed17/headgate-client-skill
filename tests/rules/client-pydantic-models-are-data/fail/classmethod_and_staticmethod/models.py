class Quote(BaseModel):
    bid: float

    @classmethod
    def empty(cls) -> "Quote":
        return cls(bid=0.0)
