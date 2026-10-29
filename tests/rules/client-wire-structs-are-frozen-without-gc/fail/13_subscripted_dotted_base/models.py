class Envelope(msgspec.Struct[T], frozen=True):
    data: T
