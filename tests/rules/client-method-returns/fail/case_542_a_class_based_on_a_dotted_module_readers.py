# A class based on a dotted AsyncBaseClient; a decorated one (the module's only client class).
# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(headgate.AsyncBaseClient):
    async def get_x(self) -> Any:
        return await self.get("x", expect=X)
