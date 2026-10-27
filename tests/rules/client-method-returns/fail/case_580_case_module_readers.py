# The same case with its readers moved to module level (R3).
A = decoder(A)


type Blob = dict[str, Any]


class C(AsyncBaseClient):
    async def get_a(self) -> Blob:
        return await self.get("a", expect=A)
