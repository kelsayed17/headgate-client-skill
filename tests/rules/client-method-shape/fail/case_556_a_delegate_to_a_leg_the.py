# A delegate to a leg the class does not define (the base's `_request`, or a missing name).
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self._missing("x")
