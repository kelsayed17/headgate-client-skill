class _InternalClient(AsyncBaseClient):
    def __init__(self, *, base_url: str = "http://internal/x") -> None:
        super().__init__(base_url=base_url, rate=Rate.per_second(1))

a = C(base_url=hosts.FRED)
b = C(base_url=_host())
c = C(base_url=f"https://{h}/v1")
