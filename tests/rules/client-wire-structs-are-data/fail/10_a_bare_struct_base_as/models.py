def build():
    class Row(msgspec.Struct):
        @functools.cached_property
        def value(self) -> float:
            return 1.0

    return Row
