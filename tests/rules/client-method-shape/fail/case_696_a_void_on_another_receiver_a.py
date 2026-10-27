# A void on another receiver; a delegate's string interpolating a bare call, and a bare await.
class C(AsyncBaseClient):
    async def cancel(self) -> None:
        await self._http.delete("x", expect=nothing)
