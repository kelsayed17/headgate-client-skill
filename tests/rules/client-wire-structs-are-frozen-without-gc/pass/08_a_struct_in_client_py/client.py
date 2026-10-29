class Cursor(msgspec.Struct, frozen=True, gc=False):
    next: str | None = None
