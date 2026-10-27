# A non-client module (no AsyncBaseClient class): its classes are not read, even `_`-based ones.
class FtpTransport(httpx2.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response: ...


class _Cursored(Protocol):
    def follow_cursor(self) -> str | None: ...


class _CorporateActionsPage(_Cursored, Protocol):
    def next_page(self) -> str | None: ...
