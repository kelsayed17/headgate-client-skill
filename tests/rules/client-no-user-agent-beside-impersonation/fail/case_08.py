async def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class C:
    async def open(self):
        await _t()
        self.h = {"User-Agent": "x"}
