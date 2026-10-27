from headgate import AsyncBaseClient, BearerAuth, CachedTokenAuth, HttpCache, StaticHeaderAuth, TransportPolicy

class ItemClient(AsyncBaseClient):  # headgate-verify: allow client-cache-with-bearer-auth -- the cache keeps the default per-credential partition and the responses are per-token on purpose
    def __init__(self, *, token: str, cache: HttpCache) -> None:
        super().__init__(base_url=BASE_URL, auth=BearerAuth(token), policy=TransportPolicy(cache=cache))
