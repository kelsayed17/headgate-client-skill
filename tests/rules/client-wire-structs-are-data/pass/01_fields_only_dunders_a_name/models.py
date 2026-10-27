class Page(msgspec.Struct, frozen=True, gc=False):
    items: list[Item]
    next_cursor: str | None = msgspec.field(name="cursor", default=None)

    def __post_init__(self) -> None:
        def _check() -> None:
            pass

    def __repr__(self) -> str:
        return "Page"

    def __mangled(self) -> None:
        pass
