def _t(transport=AsyncCurlTransport(impersonate="chrome", default_headers=True)):
    return transport


class C:
    def __init__(self):
        _t()
        self.h = {"User-Agent": "x"}
