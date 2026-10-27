FILING = decoder(Filing)


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Filing | None:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING)
