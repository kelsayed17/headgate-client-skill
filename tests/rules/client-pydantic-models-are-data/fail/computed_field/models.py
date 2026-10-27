class Quote(BaseModel):
    bid: float

    @computed_field
    @property
    def double(self) -> float:
        return self.bid * 2
