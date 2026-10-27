from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, token: str) -> None:
        super().__init__(base_url=BASE_URL, auth=BearerAuth(token), policy=TransportPolicy(cache=None))
