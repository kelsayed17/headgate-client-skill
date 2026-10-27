from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, Partition, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, storage: object) -> None:
        super().__init__(
            base_url=BASE_URL,
            policy=TransportPolicy(cache=HttpCache(storage=storage, partition=Partition.SHARED)),
        )
