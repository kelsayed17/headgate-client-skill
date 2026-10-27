from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, token: str, cache: HttpCache) -> None:
        super().__init__(
            base_url=BASE_URL,
            auth=StaticHeaderAuth({"authorization": f"Bearer {token}"}),
            policy=TransportPolicy(cache=cache),
        )
