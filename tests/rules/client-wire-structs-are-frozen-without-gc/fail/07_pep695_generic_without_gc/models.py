class Envelope[T](msgspec.Struct, kw_only=True, frozen=True):
    data: T
