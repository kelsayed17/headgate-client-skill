# `Optional` stays banned, a `nothing` answer or not: write `T | None`.
FILING_OR_NONE = Expect(decoder(Filing)).on(404, nothing)


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Optional[Filing]:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING_OR_NONE)
