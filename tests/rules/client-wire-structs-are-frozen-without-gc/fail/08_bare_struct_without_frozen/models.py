from msgspec import Struct


class Quote(Struct, rename="camel", gc=False):
    bid: float
