class C(AsyncBaseClient):
    def __getattr__(self, name: str) -> Any:
        return self._any
