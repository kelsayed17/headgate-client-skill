# A raw return under another verb (paper:468's `answer -> bytes`), on a subclass of a private base.
class _PaperEngineClient(AsyncBaseClient):
    """The construction seam; no routes."""


class PaperHistoryClient(_PaperEngineClient):
    async def answer(self, domain: str, *, body: Any | None = None) -> bytes:
        return await self.post(t"/internal/history/{domain}", json=body, expect=as_bytes)
