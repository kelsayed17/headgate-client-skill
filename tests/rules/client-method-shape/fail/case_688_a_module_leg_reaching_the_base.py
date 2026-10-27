# A module leg reaching the base's private request method; one sending a global body.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client._request("GET", path, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")
