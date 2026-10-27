class Quote(BaseModel):
    model_config = ConfigDict(frozen=True)

    bid: float
