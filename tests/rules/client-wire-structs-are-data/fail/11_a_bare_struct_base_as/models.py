class Page(msgspec.Struct):
    @property
    def follow_cursor_or_none(self) -> str | None:
        return None
