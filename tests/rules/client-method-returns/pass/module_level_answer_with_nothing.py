# A documented 404 declared at module level with `nothing` (headgate's own example): the method returns `T | None`.
from http import HTTPStatus

FILING = decoder(Filing)
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)
REPORT_OR_GONE = Expect(decoder(Report)).on(404, nothing).on(HTTPStatus.GONE, decoder(Gone))


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Filing | None:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING_OR_NONE)

    async def get_report(self, report_id: str) -> Report | Gone | None:
        return await self.get(t"reports/{report_id}", expect=REPORT_OR_GONE)

    async def get_filing_inline(self, filing_uuid: str) -> Filing | None:
        return await self.get(t"filings/{filing_uuid}/", expect=Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing))
