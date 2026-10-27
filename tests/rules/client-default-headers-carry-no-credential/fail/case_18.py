class C(AsyncBaseClient):
    _HEADERS: ClassVar[dict[str, str]] = {"X-Token": "t"}

    @classmethod
    def build(cls) -> None:
        AsyncBaseClient(http=HttpOptions(headers=cls._HEADERS))
