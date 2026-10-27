# Anywhere in a client package, a private helper or a free function handing back a Response.
async def _raw_page(client: AsyncBaseClient, url: str) -> httpx2.Response:
    return await client._http_client.get(url)
