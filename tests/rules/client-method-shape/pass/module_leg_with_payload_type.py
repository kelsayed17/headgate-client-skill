# The same module leg with a module-level reader passes (the R3 twin of fail/inline_reader_in_a_leg.py).


async def _fetch(client: AsyncBaseClient, path: str, payload: type[T]) -> T:
    return await client.get(path, expect=decoder(Report))


class C(AsyncBaseClient):
    async def get_report(self) -> Report:
        return await _fetch(self, "report", Report)
