# The same case with its readers moved to module level (R3).
ROWS = decoder(Rows)


type Rows = list[Row]
_ACCEPT = "Any object"


class _Models:
    Text = str


class C(AsyncBaseClient):
    async def get_rows(self) -> Rows:
        return await self.get("rows", expect=ROWS)
