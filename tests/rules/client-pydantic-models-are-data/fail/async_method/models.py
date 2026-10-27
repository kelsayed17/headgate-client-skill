class Quote(BaseModel):
    bid: float

    async def refresh(self) -> None:
        pass
