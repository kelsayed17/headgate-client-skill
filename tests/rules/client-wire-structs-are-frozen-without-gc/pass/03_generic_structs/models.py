class Envelope(msgspec.Struct, Generic[T], frozen=True, gc=False):
    data: T


class Page[T](msgspec.Struct, frozen=True, gc=False, kw_only=True):
    items: list[T]
