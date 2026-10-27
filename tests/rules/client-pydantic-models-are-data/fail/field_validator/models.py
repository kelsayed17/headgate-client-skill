class Quote(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", frozen=True)

    bid: float

    @field_validator("bid")
    @classmethod
    def positive(cls, value: float) -> float:
        return value
