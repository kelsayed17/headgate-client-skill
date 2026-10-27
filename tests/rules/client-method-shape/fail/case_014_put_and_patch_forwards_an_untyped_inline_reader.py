# put and patch forwards; an untyped parameter and an untyped default forwarded as bodies.
# R3: the source's inline reader; `expect=` is a module-level name here.
class AlpacaTradingClient(AsyncBaseClient):
    async def replace_order(self, order_id: str, body=None) -> Order:
        return await self.patch(t"v2/orders/{order_id}", json=body, expect=decoder(Order), retry=False)

    async def update_watchlist(self, watchlist_id: str, body: WatchlistBody) -> Watchlist:
        return await self.put(t"v2/watchlists/{watchlist_id}", body=_WRITE(body), expect=decoder(Watchlist))

    async def post_form(self, form, /) -> Ack:
        return await self.post("form", data=form, expect=decoder(Ack))
