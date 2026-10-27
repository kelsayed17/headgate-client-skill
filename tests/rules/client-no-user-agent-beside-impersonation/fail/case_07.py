def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class C:
    def __init__(self):
        self.transport = module._t()
        self.h = {"User-Agent": "x"}
