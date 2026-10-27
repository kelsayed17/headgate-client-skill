class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url="localhost:8080")
