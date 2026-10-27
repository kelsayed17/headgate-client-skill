# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def create(self, name: str, symbols: list[str]) -> X:
        return await self.post("x", body=_WRITE(PaperWatchlistCreate(name=name, symbols=symbols)), expect=X)
