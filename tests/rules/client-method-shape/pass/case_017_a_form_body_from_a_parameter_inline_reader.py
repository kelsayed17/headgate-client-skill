# A form body from a parameter's to_builtins; a headers parameter forwarded as is.
# R3: the same shape with its reader written at the call, `expect=decoder(Type)`, which is a plain type reader.
class SenateClient(AsyncBaseClient):
    async def search(self, request: SearchRequest) -> SearchPage:
        return await self.post("search/report/data/", data=to_builtins(request), expect=decoder(SearchPage))

    async def get_page(self, url: str, headers: dict[str, str]) -> bytes:
        return await self.get(url, headers=headers, expect=as_bytes)
