from headgate import AsyncBaseClient, Rate

RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self, **options: object) -> None:
        super().__init__(rate=RATE, **options)
