class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=(_A if x else ("https://h.example.org" if y else "https://h.example.org/v1")))
