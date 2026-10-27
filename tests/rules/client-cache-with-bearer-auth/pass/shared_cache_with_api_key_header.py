from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, Partition, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, key: str, storage: object) -> None:
        super().__init__(
            base_url=BASE_URL,
            auth=StaticHeaderAuth({"x-api-key": key}),
            policy=TransportPolicy(cache=HttpCache(storage=storage, partition=Partition.SHARED)),
        )
