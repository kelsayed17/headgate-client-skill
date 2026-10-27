# headgate-verify-config: {"write_name_fragments": ["place_order", "place_option_order", "place_multileg", "submit_order", "create_order", "close_position", "close_all_positions", "close_option_position", "liquidat", "modify_order", "edit_order", "exercise_options", "cancel_order"]}
# retry= named (False, or any value: the kept test_order_placement_no_retry.py requires False); a read or a
# non-self write inside an executing method; a write inside a method that is not executing, a cancel, a preview.
class AlpacaClient(AsyncBaseClient):
    async def submit_order(self, body: OrderBody) -> Order:
        return await self.post("/v2/orders", json=to_builtins(body), expect=decoder(Order), retry=False)

    async def replace_order_by_id(self, order_id: str, body: Patch) -> Order:
        return await self.patch(t"/v2/orders/{order_id}", json=to_builtins(body), retry=True)

    async def close_position(self, symbol: str) -> Order:
        await self.get(t"/v2/positions/{symbol}")
        await self._post(t"/v2/positions/{symbol}")
        await super().post(t"/v2/positions/{symbol}")
        return await other.delete(t"/v2/positions/{symbol}")

    async def update_watchlist(self, body: Watchlist) -> Watchlist:
        return await self.put("/v2/watchlists", json=to_builtins(body))

    async def cancel_order(self, order_id: str) -> None:
        await self.delete(t"/v2/orders/{order_id}")

    async def preview_place_order(self, body: OrderBody) -> Preview:
        return await self.post("/v2/orders/preview", json=to_builtins(body))
