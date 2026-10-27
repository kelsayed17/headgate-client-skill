# headers= is never a dict literal, a header helper takes only parameters, and a per-call cache_ttl= is a literal
# or a parameter, never a value the method computes.
class CboeClient(AsyncBaseClient):
    async def fetch_put_call_daily_html(self) -> bytes:
        return await self.get(
            "us/options/market_statistics/daily/",
            expect=as_bytes,
            timeout=60,
            headers={"User-Agent": _BROWSER_UA, "Accept": "text/html,application/xhtml+xml,*/*"},
        )
