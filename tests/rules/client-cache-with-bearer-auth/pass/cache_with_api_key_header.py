from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, key: str, cache: HttpCache) -> None:
        super().__init__(
            base_url=BASE_URL, auth=StaticHeaderAuth({"x-api-key": key}), policy=TransportPolicy(cache=cache)
        )
