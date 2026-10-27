class C(AsyncBaseClient):
    def __init__(self) -> None:
        base = "https://api.example.org/v1"
        super().__init__(base_url=base)
