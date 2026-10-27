from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, basic: str, cache: HttpCache) -> None:
        super().__init__(
            base_url=BASE_URL, auth=StaticHeaderAuth({"Authorization": f"Basic {basic}"}), policy=TransportPolicy(cache=cache)
        )
