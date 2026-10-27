# A second request hidden in a tuple: after a void, and posing as the docstring.
class C(AsyncBaseClient):
    async def cancel(self) -> None:
        await self.delete("x", expect=nothing), await self.delete("y", expect=nothing)
