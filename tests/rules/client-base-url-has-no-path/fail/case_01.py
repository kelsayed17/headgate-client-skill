class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url="https://api.example.org/v1", rate=Rate.per_second(1))
