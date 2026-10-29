class C(AsyncBaseClient):
    async def get_x(self, **params: Any) -> X:
        return await self._leg(**params)
