class Envelope(BaseModel):
    class Row(BaseModel):
        def value(self) -> float:
            return 1.0
