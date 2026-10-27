class Quote(BaseModel):
    bid: float

    def model_post_init(self, context: object) -> None:
        pass
