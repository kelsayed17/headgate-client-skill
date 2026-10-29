class Envelope(msgspec.Struct, Generic[T], frozen=True):
    data: T
