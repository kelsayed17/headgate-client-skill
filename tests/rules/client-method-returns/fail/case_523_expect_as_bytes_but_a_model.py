# expect=as_bytes but a model returned (paper:309's shape), and a return alias of bytes.
class _PaperEngineClient(AsyncBaseClient):
    """The construction seam; no routes."""


class PaperBrokerageClient(_PaperEngineClient):
    async def place_option_order(self, user_id: UUID, request: OptionOrderRequest) -> PaperOrder:
        body = await self.post("/api/brokerage/options/orders", json=to_builtins(request), retry=False, expect=as_bytes)
        if not body or body.strip() == b"null":
            raise OrderDeclined("declined", source=type(self).__name__)
        return decode(body, PaperOrder)
