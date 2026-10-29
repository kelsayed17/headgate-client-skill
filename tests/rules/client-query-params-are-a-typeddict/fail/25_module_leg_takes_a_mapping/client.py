async def _fetch(client: AsyncBaseClient, path: str, params: Mapping[str, object] | None = None) -> bytes:
    return await client.get(path, expect=as_bytes, params=params)
