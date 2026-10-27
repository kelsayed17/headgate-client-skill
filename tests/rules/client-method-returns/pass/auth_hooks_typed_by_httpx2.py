# headgate's auth hooks are typed by httpx2's auth flow: their annotations name Response.
class ShopTokenAuth(CachedTokenAuth):
    async def mint_flow(self, request: httpx2.Request) -> AsyncGenerator[httpx2.Request | Minted[str], httpx2.Response]:
        response = yield httpx2.Request("POST", MINT_ENDPOINT, data=self._form)
        yield Minted(response.text, 60.0)


class SyncAuth(httpx2.Auth):
    def auth_flow(self, request: httpx2.Request) -> Generator[httpx2.Request, httpx2.Response]:
        yield request
