# Two statements: work before the request (bls:71).
# Readers moved to module level (R3).
BLS_RESPONSE = decoder(BlsResponse)


class BlsClient(AsyncBaseClient):
    async def get_series_chunk(self, request: BlsSeriesRequest) -> BlsResponse:
        body = msgspec.structs.replace(request, registrationkey=self._api_key or None)
        return await self.post("publicAPI/v2/timeseries/data/", body=_WRITE(body), expect=BLS_RESPONSE)
