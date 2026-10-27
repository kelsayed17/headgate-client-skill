# A void write, `headers=self._uid(...)`, and a void written as `return await`.
class _PaperEngineClient(AsyncBaseClient):
    """The construction seam; no routes."""


class PaperBrokerageClient(_PaperEngineClient):
    async def reset(self, user_id: UUID) -> None:
        """``POST /api/brokerage/options/reset``."""
        await self.post("/api/brokerage/options/reset", headers=self._uid(user_id), expect=nothing)

    async def cancel(self, order_id: str) -> None:
        return await self.delete(t"v2/orders/{order_id}", expect=nothing, retry=False)

    async def check_available(self) -> None:
        await self.head(STATUS_PATH, expect=nothing, timeout=_PROBE_TIMEOUT)
