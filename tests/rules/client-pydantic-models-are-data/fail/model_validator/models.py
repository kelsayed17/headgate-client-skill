class Quote(BaseModel):
    bid: float
    ask: float

    @model_validator(mode="after")
    def ordered(self) -> "Quote":
        return self
