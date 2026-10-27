# The rss module function leg, with and without the params collector.
async def _fetch_feed(
    client: AsyncBaseClient, path: str | Template, params: Mapping[str, object] | None = None
) -> bytes:
    """Fetch one feed document and return its body bytes."""
    return await client.get(path, expect=as_bytes, params=params)


class CnbcClient(AsyncBaseClient):
    async def fetch_combined_cms_bytes(self, **params: Unpack[CnbcFeedParams]) -> bytes:
        """``GET /`` — one feed."""
        return await _fetch_feed(self, "view.xml", params)


class InvestingClient(AsyncBaseClient):
    async def fetch_news_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "news.rss")
