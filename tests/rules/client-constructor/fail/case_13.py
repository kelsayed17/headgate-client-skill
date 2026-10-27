class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            policy=TransportPolicy(rate_limits=(RateRule("candles", Rate.per_second(_CANDLES_MAX_RATE_PER_SEC)),)),
        )
