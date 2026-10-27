async def _post_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.post(path, json=_BODY, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _post_feed(self, "feed/")
