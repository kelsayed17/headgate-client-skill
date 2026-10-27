# `as_bytes` returns `bytes`, inline or as the root of a module-level chain; the method's name is free (the source's
# `fetch_` naming clause does not port: the naming check owns names).
from http import HTTPStatus

RAW_OR_NONE = Expect(as_bytes).on(HTTPStatus.NOT_FOUND, nothing)


class C(AsyncBaseClient):
    async def get_report_csv(self) -> bytes:
        return await self.get("report.csv", expect=as_bytes)

    async def get_export(self) -> bytes | None:
        return await self.get("export.zip", expect=RAW_OR_NONE)
