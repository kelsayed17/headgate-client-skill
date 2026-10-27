# A public module function as the leg, and a module leg handed a parameter instead of `self`.
async def fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class CnbcClient(AsyncBaseClient):
    async def fetch_feed_bytes(self) -> bytes:
        return await fetch_feed(self, "feed/")
