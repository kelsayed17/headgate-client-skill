# `as_bytes` behind `-> bytes` and behind `-> bytes | None` (a module chain with a `nothing` answer): a raw return
# whatever the method is named.
from http import HTTPStatus

RAW_OR_NONE = Expect(as_bytes).on(HTTPStatus.NOT_FOUND, nothing)


class C(AsyncBaseClient):
    async def get_report_csv(self) -> bytes:
        return await self.get("report.csv", expect=as_bytes)

    async def get_export(self) -> bytes | None:
        return await self.get("export.zip", expect=RAW_OR_NONE)
