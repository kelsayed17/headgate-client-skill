# The raw wire: fetch_ -> bytes, directly and through the rss module leg.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class CftcClient(AsyncBaseClient):
    async def fetch_tff_current_week(self) -> bytes:
        return await self.get(TFF_CURRENT_PATH, expect=as_bytes, timeout=60)

    async def fetch_news_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "news.rss")
