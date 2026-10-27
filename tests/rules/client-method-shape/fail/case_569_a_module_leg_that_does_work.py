# A module leg that does work, that is missing, that is not handed `self`, or that forwards on a
# receiver other than its first parameter.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    body = await client.get(path, expect=as_bytes)
    return body.strip()


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")
