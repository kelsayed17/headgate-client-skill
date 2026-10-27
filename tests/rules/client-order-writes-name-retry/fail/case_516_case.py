# headgate-verify-config: {"write_name_fragments": ["place_order", "place_option_order", "place_multileg", "submit_order", "create_order", "close_position", "close_all_positions", "close_option_position", "liquidat", "modify_order", "edit_order", "exercise_options", "cancel_order"]}
async def place_order(self, order_id):
    return await self.delete(t"/orders/{order_id}")
