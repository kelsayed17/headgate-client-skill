class C(AsyncBaseClient):
    async def fetch_x(self, **params: Unpack[XParams]) -> bytes:
        return await self.get("x", params=params, expect=as_bytes, cache_ttl=_ttl(params["date"], params.get("kind")))
