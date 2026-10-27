# A union alias without None is a model union.
# The same case with its readers moved to module level (R3).
PAYLOAD = decoder(Payload)


Payload = Quote | Trade


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=PAYLOAD)
