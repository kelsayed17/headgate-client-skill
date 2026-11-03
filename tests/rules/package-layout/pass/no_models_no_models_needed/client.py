from headgate import AsyncBaseClient, Rate, as_bytes

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    async def fetch_report(self) -> bytes:
        return await self.get("report", expect=as_bytes)
