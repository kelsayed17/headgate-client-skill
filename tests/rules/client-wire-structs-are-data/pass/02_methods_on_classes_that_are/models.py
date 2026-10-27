class PagedFetch(Protocol):
    async def __call__(self, cursor: str | None) -> Page: ...

    def follow_cursor(self) -> str | None: ...

    def items(self) -> list[Item]: ...


class Body(TypedDict):
    def render(self) -> str: ...


class Side(enum.Enum):
    def flip(self) -> Side: ...


class Meta(msgspec.StructMeta):
    def build(self) -> None: ...


class Structured(Base):
    def build(self) -> None: ...


class Struct:
    def build(self) -> None: ...


class Config(Struct.Config):
    def build(self) -> None: ...


def module_level(page: Page) -> int:
    return len(page.items)
