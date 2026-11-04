# Out of scope: private methods and module legs may read raw bytes (a public method decodes what they return); a
# class that is not a transport class; an alias of `bytes` that no public method returns; names that only contain
# `fetch`.
Raw = bytes


async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class Helper:
    def fetch_bytes(self) -> bytes:
        return b""


class C(AsyncBaseClient):
    async def _fetch_raw(self, path: str) -> Raw:
        return await self.get(path, expect=as_bytes)

    async def get_fetch_status(self) -> FetchStatus:
        return await self.get("fetch/status", expect=decoder(FetchStatus))

    async def fetcher_state(self) -> FetcherState:
        return await self.get("fetcher", expect=decoder(FetcherState))
