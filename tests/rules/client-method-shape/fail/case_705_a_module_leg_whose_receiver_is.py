# A module leg whose receiver is not its first parameter; `self` handed in second.
async def _fetch_feed(path: str, client: AsyncBaseClient) -> bytes:
    return await client.get(path, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")
