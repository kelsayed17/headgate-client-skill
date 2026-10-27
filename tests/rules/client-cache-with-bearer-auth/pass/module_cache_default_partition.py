from headgate import AsyncBaseClient, BearerAuth, HttpCache, Partition, TransportPolicy

CACHE = HttpCache(storage=None)
POLICY = TransportPolicy(cache=CACHE)


class ItemClient(AsyncBaseClient):
    def __init__(self, *, token: str) -> None:
        super().__init__(base_url=BASE_URL, auth=BearerAuth(token), policy=POLICY)
