class C:
    def __init__(self):
        self._transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)

    def headers(self):
        def inner():
            return {"User-Agent": "x"}

        return inner()
