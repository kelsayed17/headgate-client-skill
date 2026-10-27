# headgate-verify-config: {"write_name_fragments": ["place_order", "place_option_order", "place_multileg", "submit_order", "create_order", "close_position", "close_all_positions", "close_option_position", "liquidat", "modify_order", "edit_order", "exercise_options", "cancel_order"]}
# A fragment inside a longer or private name; a sync def; a write in a nested def or a lambda inside one; a
# parenthesised callee; retry arriving only through **kwargs.
async def _close_position_by_id(self, position_id):
    return await self.delete(t"/positions/{position_id}")
