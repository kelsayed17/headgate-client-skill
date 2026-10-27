# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, live: bool) -> X:
        return await (self.get("live", expect=X) if live else self.get("paper", expect=X))
