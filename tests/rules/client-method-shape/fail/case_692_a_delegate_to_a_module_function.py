# A delegate to a module function that does not exist beside one that does; a global in its arguments; a
# delegate to the module's non-conforming leg beside a conforming one.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_other(self, "feed/")
