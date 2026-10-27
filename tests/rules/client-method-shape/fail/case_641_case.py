async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    """One feed."""
    return await client.get(path, expect=as_bytes)
    client.calls += 1


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")
