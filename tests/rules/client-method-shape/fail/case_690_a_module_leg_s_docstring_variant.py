# A module leg's docstring variant: a statement before the forward; a docstring and no forward.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    client.calls += 1
    return await client.get(path, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")
