# A module with no AsyncBaseClient class is not a client module (R12 keeps transport classes in client.py):
# a pagination Protocol over a `_` base is not read. The collector clause still reads every module.
class FtpTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response: ...


class _Cursored(Protocol):
    def follow_cursor(self) -> str | None: ...


class _CorporateActionsPage(_Cursored, Protocol):
    announcements: list[Announcement]

    def next_page(self) -> str | None: ...


async def all_rows(fetch: Fetch, *call_args: object, **params: Unpack[RowsParams]) -> list[Row]:
    return [row async for page in _walk(fetch, *call_args, **params) for row in page.rows]
