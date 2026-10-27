# Readers moved to module level (R3).
X = decoder(X)


class Public(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)


class Sub(Public):
    _BASE: ClassVar[str] = _OTHER
