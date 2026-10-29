class C(AsyncBaseClient):
    async def get_x(self, **params: Unpack[XParams]) -> X:
        self._seen[params["date"]] = True
        self._hits[params["date"]] += 1
        del self._cache[params["date"]]
        for self._last[params["date"]] in ():
            pass
        return await self.get("x", params=params, expect=decoder(X))
