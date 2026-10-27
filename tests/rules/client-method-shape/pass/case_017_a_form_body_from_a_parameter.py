# A form body from a parameter's to_builtins; a headers parameter forwarded as is.
# Readers moved to module level (R3).
SEARCH_PAGE = decoder(SearchPage)


class SenateClient(AsyncBaseClient):
    async def search(self, request: SearchRequest) -> SearchPage:
        return await self.post("search/report/data/", data=to_builtins(request), expect=SEARCH_PAGE)

    async def get_page(self, url: str, headers: dict[str, str]) -> bytes:
        return await self.get(url, headers=headers, expect=as_bytes)
