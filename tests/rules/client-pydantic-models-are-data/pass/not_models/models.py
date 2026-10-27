class PagedFetch(Protocol):
    async def __call__(self, cursor: str | None) -> Page: ...

    def items(self) -> list[Item]: ...


class Body(TypedDict):
    def render(self) -> str: ...


class Side(enum.Enum):
    def flip(self) -> Side: ...


class Meta(pydantic.BaseModelMeta):
    def build(self) -> None: ...


class Structured(Base):
    def build(self) -> None: ...


class BaseModel:
    def build(self) -> None: ...


def module_level(model: Quote) -> float:
    return model.bid
