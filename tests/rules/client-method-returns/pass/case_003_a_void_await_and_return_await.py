# A void: `await` and `return await`, the write and the HEAD probe.
class Brokerage(AsyncBaseClient):
    async def reset(self, user_id: UUID) -> None:
        """A void write."""
        await self.post("/api/brokerage/options/reset", headers=self._uid(user_id), expect=nothing)

    async def cancel(self, order_id: str) -> None:
        return await self.delete(t"v2/orders/{order_id}", expect=nothing, retry=False)

    async def check_available(self) -> None:
        await self.head(STATUS_PATH, expect=nothing, timeout=10)
