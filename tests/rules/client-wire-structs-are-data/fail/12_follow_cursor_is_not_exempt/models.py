class Page(msgspec.Struct):
    next_cursor: str | None = None

    @property
    def follow_cursor(self) -> str | None:
        return self.next_cursor
