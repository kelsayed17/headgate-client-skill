# R3 holds in a module leg: a reader built from a parameter is a reader built per call.
async def _fetch(client: AsyncBaseClient, path: str, payload: type[T]) -> T:
    return await client.get(path, expect=decoder(payload))


class C(AsyncBaseClient):
    async def get_report(self) -> Report:
        return await _fetch(self, "report", Report)
