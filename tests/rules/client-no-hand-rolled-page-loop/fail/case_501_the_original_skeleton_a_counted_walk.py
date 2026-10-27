# The original skeleton: a counted walk on self, and an unbounded one.
class FinraClient(AsyncBaseClient):
    async def get_all(self) -> list[Row]:
        rows = []
        for _ in range(_MAX_PAGES):
            page = await self.post("/data", json=body)
            rows += page.rows
        return rows
