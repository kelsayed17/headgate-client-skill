class C(AsyncBaseClient):
    async def _exchange(self, request: Any) -> Any:
        return await super()._exchange(request)
