async def _fetch_feed(client: AsyncBaseClient, path: str, params: Params | None = None) -> bytes:
    return await client.get(path, params=params, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/", _DEFAULT_PARAMS)
