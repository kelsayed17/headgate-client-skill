# Readers moved to module level (R3).
ENVELOPE = decoder(Envelope)


class C(AsyncBaseClient):
    async def get_x(self) -> list[Row]:
        return await self.get("x", expect=ENVELOPE).data
