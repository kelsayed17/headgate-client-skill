# headgate-verify-config: {"write_name_fragments": ["place_order", "place_option_order", "place_multileg", "submit_order", "create_order", "close_position", "close_all_positions", "close_option_position", "liquidat", "modify_order", "edit_order", "exercise_options", "cancel_order"]}
# Callees that are not a self write: an attribute OF one, a parenthesised private, a parenthesised conditional; a
# write in a non-executing method whose PARAMETER or keyword merely carries a fragment.
class C(AsyncBaseClient):
    async def place_order(self, body):
        await self.delete.__wrapped__(self, "/orders")
        await (self._request)(call, expect)
        return await (self.post if body.new else self.put)("/orders", json=body)

    async def run(self, place_order_hint=None):
        return dispatch(close_position=self.post("/x"))
