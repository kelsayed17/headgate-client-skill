class Cursor(msgspec.Struct, frozen=True):
    next: str | None = None
