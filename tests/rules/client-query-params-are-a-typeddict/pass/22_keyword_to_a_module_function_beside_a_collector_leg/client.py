def _ttl(*, year: int) -> int:
    return 86400 if year < 2020 else 3600


async def _fetch(client: AsyncBaseClient, path: str, **params: Unpack[XParams]) -> bytes:
    return await client.get(path, params=params, expect=as_bytes, cache_ttl=_ttl(year=2024))


class C(AsyncBaseClient):
    async def fetch_x(self, **params: Unpack[XParams]) -> bytes:
        return await _fetch(self, "x", **params)
