class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_HOST + "/v1", rate=Rate.per_second(_MAX_RATE_PER_SEC))
