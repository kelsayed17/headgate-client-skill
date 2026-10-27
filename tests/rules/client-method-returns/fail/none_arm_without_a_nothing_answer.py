# `| None` with no `nothing` answer declared: the reader never returns None.
FILING = decoder(Filing)
FILING_OR_GONE = Expect(FILING).on(410, decoder(Gone))


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Filing | Gone | None:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING_OR_GONE)
