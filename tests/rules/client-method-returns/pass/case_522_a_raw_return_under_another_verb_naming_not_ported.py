# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
# A raw return under another verb (paper:468's `answer -> bytes`).
class _PaperEngineClient(AsyncBaseClient):
    """The construction seam; no routes."""


class PaperHistoryClient(_PaperEngineClient):
    async def answer(self, domain: str, *, body: Any | None = None) -> bytes:
        return await self.post(t"/internal/history/{domain}", json=body, expect=as_bytes)
