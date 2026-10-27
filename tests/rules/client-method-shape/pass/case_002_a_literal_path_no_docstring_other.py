# A literal path, no docstring, other plain keywords.
class CftcClient(AsyncBaseClient):
    async def fetch_tff_current_week(self) -> bytes:
        return await self.get(TFF_CURRENT_PATH, expect=as_bytes, timeout=LONG_READ)
