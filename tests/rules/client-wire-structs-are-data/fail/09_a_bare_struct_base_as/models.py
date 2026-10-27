class Envelope(msgspec.Struct):
    class Row(msgspec.Struct):
        def value(self) -> float:
            return 1.0
