def build():
    class Row(BaseModel):
        @cached_property
        def value(self) -> float:
            return 1.0

    return Row
