class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=r"https://h.example.org/v1")
