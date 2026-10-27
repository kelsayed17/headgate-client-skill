# A reader that declares a `nothing` answer returns None on that status, so the annotation has a `None` arm.
FILING_OR_NONE = Expect(decoder(Filing)).on(HTTPStatus.NOT_FOUND, nothing)


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Filing:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING_OR_NONE)
