# I1: a request model built from scalars is not an envelope, whatever the leg does with it next; nor is the
# envelope with a literal in it.
# Readers moved to module level (R3).
PAPER_WATCHLIST = decoder(PaperWatchlist)


class C(AsyncBaseClient):
    async def create_watchlist(self, user_id: UUID, name: str, symbols: list[str]) -> PaperWatchlist:
        return await self._create(user_id, name, symbols)

    async def _create(self, user_id: UUID, name: str, symbols: list[str]) -> PaperWatchlist:
        body = PaperWatchlistCreate(name=name, symbols=symbols)
        return await self.post("/api/brokerage/watchlists", body=_WRITE(body), headers=self._uid(user_id), expect=PAPER_WATCHLIST)
