# Every legitimate body form: a writer of a parameter (`body=_WRITE(x)`, headgate 0.6.0's encoder), a bare
# parameter as json=, a writer of the collector, form data from the collector or a named parameter.
# Readers moved to module level (R3).
ORDER = decoder(Order)
WATCHLIST = decoder(Watchlist)
ACCESS_TOKEN = decoder(AccessToken)
TOKEN_RESPONSE = decoder(TokenResponse)
MESSAGE_RESOURCE = decoder(MessageResource)
RESULT = decoder(list[Result])


class Brokerage(AsyncBaseClient):
    async def place_order(self, user_id: UUID, request: OrderRequest) -> Order:
        return await self.post(
            "/api/brokerage/orders",
            body=_WRITE(request),
            headers=self._uid(user_id),
            retry=False,
            expect=ORDER,
        )

    async def update(self, watchlist_id: str, body: WatchlistBody) -> Watchlist:
        return await self.post(t"/v2/watchlists/{watchlist_id}", body=_WRITE(body), expect=WATCHLIST)

    async def answer(self, domain: str, *, body: Any | None = None) -> bytes:
        return await self.post(t"/internal/history/{domain}", json=body, expect=as_bytes)

    async def create_access_token(self, **params: Unpack[TokenParams]) -> AccessToken:
        return await self.post("/access-tokens", body=_WRITE(params), expect=ACCESS_TOKEN)

    async def exchange(self, **params: Unpack[TokenParams]) -> TokenResponse:
        return await self.post("oauth2/token/", data=params, expect=TOKEN_RESPONSE, retry=False)

    async def send_message(self, form: dict[str, str]) -> MessageResource:
        return await self.post(
            t"2010-04-01/Accounts/{self._account_sid}/Messages.json",
            expect=MESSAGE_RESOURCE,
            data=form,
            retry=False,
        )

    async def batch(self, queries: list[Query], /) -> list[Result]:
        return await self.post("v3/mapping", body=_WRITE(queries), expect=RESULT)
