import headgate


class ItemClient(headgate.AsyncBaseClient):
    def __init__(self, *, token: str, cache: headgate.HttpCache) -> None:
        super().__init__(
            base_url=BASE_URL, auth=headgate.BearerAuth(token), policy=headgate.TransportPolicy(cache=cache)
        )
