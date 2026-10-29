from msgspec import Struct


class Envelope(Struct[T], frozen=True):
    data: T
