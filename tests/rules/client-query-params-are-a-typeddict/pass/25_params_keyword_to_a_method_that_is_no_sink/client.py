class C(AsyncBaseClient):
    def _encoded(self, symbol: str) -> bytes:
        return self._codec.encode(params={"symbol": symbol})
