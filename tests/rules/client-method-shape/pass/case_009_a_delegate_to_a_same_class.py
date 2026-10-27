# A delegate to a same-class private leg that is itself a direct forward (arm c).
# Readers moved to module level (R3).
SERIES_RESPONSE = decoder(SeriesResponse)


class Series(AsyncBaseClient):
    async def get_series_marts(self, **params: Unpack[SeriesParams]) -> SeriesResponse:
        return await self._series(t"marts", **params)

    async def _series(self, dataset: str, **params: Unpack[SeriesParams]) -> SeriesResponse:
        return await self.get(t"{dataset}/series", params=params, expect=SERIES_RESPONSE)
