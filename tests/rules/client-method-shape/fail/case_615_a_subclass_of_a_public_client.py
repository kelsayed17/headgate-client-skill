# A subclass of a PUBLIC client, here and imported.
# Readers moved to module level (R3).
X = decoder(X)


class PublicClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)


class Sub(PublicClient):
    _BASE: ClassVar[str] = _OTHER
