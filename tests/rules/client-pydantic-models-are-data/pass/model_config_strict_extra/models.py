class Quote(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", frozen=True)

    bid: float = Field(alias="b")
    tags: ClassVar[tuple[str, ...]] = ("a",)
