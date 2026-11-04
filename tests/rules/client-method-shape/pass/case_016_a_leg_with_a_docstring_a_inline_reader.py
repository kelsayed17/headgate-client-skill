# A leg with a docstring; a module leg without one; a `**kwargs: Any` pass-through is not a collector.
# R3: the same shape with its reader written at the call, `expect=decoder(Type)`, which is a plain type reader.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class Series(AsyncBaseClient):
    async def get_series_marts(self, **params: Unpack[SeriesParams]) -> SeriesResponse:
        """One dataset."""
        return await self._series(t"marts", **params)

    async def _series(self, dataset: str, **params: Unpack[SeriesParams]) -> SeriesResponse:
        """The shared leg of the seven dataset methods."""
        return await self.get(t"{dataset}/series", params=params, expect=decoder(SeriesResponse))

    async def fetch_feed_bytes(self) -> bytes:
        return await _fetch_feed(self, "feed/")

    async def _passthrough(self, method: str, url: str, **kwargs: Any) -> bytes:
        return await self._request(method, url, expect=as_bytes, **kwargs)
