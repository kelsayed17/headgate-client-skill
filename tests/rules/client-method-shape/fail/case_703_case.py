# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, arguments: Args) -> X:
        return await self._leg(arguments=_DEFAULT_ARGUMENTS)

    async def _leg(self, arguments: Args) -> X:
        return await self.post("x", body=_WRITE(arguments), expect=X)
