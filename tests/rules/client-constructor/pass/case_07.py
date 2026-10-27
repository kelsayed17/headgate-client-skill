class CoinbaseClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            rate=Rate.per_second(_MAX_RATE_PER_SEC),
            policy=TransportPolicy(
                retry=RETRY_EVERY_METHOD,
                rate_limits=(RateRule("candles", Rate.per_second(_CANDLES_MAX_RATE_PER_SEC)),),
            ),
            http=HttpOptions(transport=AsyncCurlTransport(impersonate="chrome", default_headers=True)),
        )
