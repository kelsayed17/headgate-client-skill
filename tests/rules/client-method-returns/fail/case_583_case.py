Loose = dict


class C(AsyncBaseClient):
    async def get_a(self) -> Loose:
        return await self.get("a", expect=decoder(A))
