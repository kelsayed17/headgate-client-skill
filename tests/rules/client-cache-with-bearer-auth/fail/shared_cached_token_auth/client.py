from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, Partition, StaticHeaderAuth, TransportPolicy

class _Mint(CachedTokenAuth):
    async def mint_token(self) -> tuple[str, float]:
        return "t", 3600.0


class ItemClient(AsyncBaseClient):
    def __init__(self, *, storage: object) -> None:
        super().__init__(
            base_url=BASE_URL,
            auth=_Mint(),
            policy=TransportPolicy(cache=HttpCache(storage=storage, partition=Partition.SHARED)),
        )
