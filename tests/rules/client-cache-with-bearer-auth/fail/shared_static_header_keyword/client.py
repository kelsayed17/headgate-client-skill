from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, Partition, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):
    def __init__(self, *, token: str, storage: object) -> None:
        super().__init__(
            base_url=BASE_URL,
            auth=StaticHeaderAuth(headers={"Authorization": f"Bearer {token}"}),
            policy=TransportPolicy(cache=HttpCache(storage=storage, partition=Partition.SHARED)),
        )
