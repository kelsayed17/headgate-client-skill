from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):  # headgate-verify: allow client-cache-with-bearer-auth -- the responses are public, the same for every token
    def __init__(self, *, token: str, storage: object) -> None:
        super().__init__(base_url=BASE_URL, auth=BearerAuth(token), policy=TransportPolicy(cache=HttpCache(storage=storage, partition=Partition.SHARED)))
