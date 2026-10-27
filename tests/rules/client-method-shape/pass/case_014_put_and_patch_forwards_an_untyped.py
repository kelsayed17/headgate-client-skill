# put and patch forwards; an untyped parameter and an untyped default forwarded as bodies.
# Readers moved to module level (R3).
ORDER = decoder(Order)
WATCHLIST = decoder(Watchlist)
ACK = decoder(Ack)


class AlpacaTradingClient(AsyncBaseClient):
    async def replace_order(self, order_id: str, body=None) -> Order:
        return await self.patch(t"v2/orders/{order_id}", json=body, expect=ORDER, retry=False)

    async def update_watchlist(self, watchlist_id: str, body: WatchlistBody) -> Watchlist:
        return await self.put(t"v2/watchlists/{watchlist_id}", body=_WRITE(body), expect=WATCHLIST)

    async def post_form(self, form, /) -> Ack:
        return await self.post("form", data=form, expect=ACK)
