class Filing(pydantic.BaseModel):
    model_config = ConfigDict(frozen=True)


class Box(typing.Generic[T]):
    item: T
