class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        count = 0

        def bump() -> None:
            nonlocal count
            count += 1

        bump()
        return await self.get("x", params=params, expect=decoder(X))
