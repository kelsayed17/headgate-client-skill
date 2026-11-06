# R3: `expect=` names a module-level reader: assigned here (public or `_`, annotated or not), imported, or one of
# headgate's own readers `nothing` and `as_bytes`.
from http import HTTPStatus

from headgate import AsyncBaseClient, Expect, as_bytes, nothing
from headgate.msgspec import decoder

from .readers import ORDER_PAGE, SHARED as SHARED_READER

FILING = decoder(Filing)
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)
_REPORT: Reader[Report] = decoder(Report)


class Lda(AsyncBaseClient):
    async def get_filing(self, filing_uuid: str) -> Filing | None:
        return await self.get(t"filings/{filing_uuid}/", expect=FILING_OR_NONE)

    async def get_report(self) -> Report:
        return await self.get("report/", expect=_REPORT)

    async def get_orders(self) -> OrderPage:
        return await self.get("orders/", expect=ORDER_PAGE)

    async def get_shared(self) -> Shared:
        return await self.get("shared/", expect=SHARED_READER)

    async def get_raw(self) -> bytes:
        return await self.get("raw/", expect=as_bytes)

    async def delete_filing(self, filing_uuid: str) -> None:
        await self.delete(t"filings/{filing_uuid}/", expect=nothing)
