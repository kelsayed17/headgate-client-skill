X_OR_ERROR = Expect(decoder(X)).on(400, decoder(dict[str, Any]))


class C(AsyncBaseClient):
    async def get_x(self) -> X | dict[str, Any]:
        return await self.get("x", expect=X_OR_ERROR)
