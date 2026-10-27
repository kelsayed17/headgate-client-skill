# A union alias without None is a model union.
Payload = Quote | Trade


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=decoder(Payload))
