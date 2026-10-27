from headgate import AsyncBaseClient, Rate

RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url="https://api.one.example", rate=RATE)
