# No wire at all.
class C(AsyncBaseClient):
    async def get_x(self) -> list[X]:
        """Nothing."""
        return []
