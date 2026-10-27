class OccClient(AsyncBaseClient):
    async def fetch_contract_volume_bytes(self, **params: Unpack[BulkParams]) -> bytes:
        return await self.get(
            OCC_BULK_PATH,
            params=params,
            timeout=60,
            cache_ttl=self._bulk_ttl(params["reportDate"]),
            expect=as_bytes,
        )
