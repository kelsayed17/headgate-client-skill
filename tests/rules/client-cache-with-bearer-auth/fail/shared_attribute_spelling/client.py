import headgate


class ItemClient(headgate.AsyncBaseClient):
    def __init__(self, *, token: str, storage: object) -> None:
        super().__init__(
            base_url=BASE_URL,
            auth=headgate.BearerAuth(token),
            policy=headgate.TransportPolicy(cache=headgate.HttpCache(storage=storage, partition=headgate.Partition.SHARED)),
        )
