# Readers moved to module level (R3).
X = decoder(X)


async def _walk(client: AsyncBaseClient, **kw: Unpack[P]) -> X:
    return await client.get("x", params=kw, expect=X)
