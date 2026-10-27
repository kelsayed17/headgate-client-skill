async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


async def _fetch_bad(client: AsyncBaseClient, path: str) -> bytes:
    return (await client.get(path, expect=as_bytes)).strip()


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_bad(self, "feed/")
