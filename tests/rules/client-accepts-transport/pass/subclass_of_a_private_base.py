class _Base(AsyncBaseClient):
    def __init__(self, *, token: str, transport: Transport | None = None) -> None:
        super().__init__(base_url=_BASE_URL, auth=BearerAuth(token), http=HttpOptions(transport=transport))


class Concrete(_Base):
    def __init__(self, *, token: str, transport: Transport | None = None) -> None:
        super().__init__(token=token, transport=transport)
