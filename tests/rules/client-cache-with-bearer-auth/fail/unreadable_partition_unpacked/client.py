from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, Partition, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, token: str, options: dict) -> None:
        super().__init__(
            base_url=BASE_URL, auth=BearerAuth(token), policy=TransportPolicy(cache=HttpCache(**options))
        )
