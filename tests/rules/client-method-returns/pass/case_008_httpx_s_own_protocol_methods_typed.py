# httpx's own protocol methods, typed by httpx: a transport and an auth flow.
class FtpTransport(httpx2.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200)


class CoinbaseAuth(httpx2.Auth):
    async def async_auth_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request, httpx2.Response]:
        yield request
