from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, cache: HttpCache) -> None:
        super().__init__(base_url=BASE_URL, policy=TransportPolicy(cache=cache))
