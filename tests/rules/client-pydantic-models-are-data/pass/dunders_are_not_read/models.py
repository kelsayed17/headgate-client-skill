class Quote(BaseModel):
    bid: float

    def __repr__(self) -> str:
        return "Quote"

    def __mangled(self) -> None:
        pass
