from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class _Mint(CachedTokenAuth):
    token_headers = frozenset({"X-Token"})

    async def mint_token(self) -> tuple[str, float]:
        return "t", 3600.0


class ItemClient(AsyncBaseClient):
    def __init__(self, *, cache: HttpCache) -> None:
        super().__init__(base_url=BASE_URL, auth=_Mint(), policy=TransportPolicy(cache=cache))
