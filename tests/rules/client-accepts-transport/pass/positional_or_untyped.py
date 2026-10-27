class A(AsyncBaseClient):
    def __init__(self, transport=None) -> None:
        super().__init__(base_url=_BASE_URL, http=HttpOptions(transport=transport))


class B(AsyncBaseClient):
    def __init__(self, transport: Transport) -> None:
        super().__init__(base_url=_BASE_URL, http=headgate.HttpOptions(timeout=_TIMEOUT, transport=transport))
