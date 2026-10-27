def _t():
    return AsyncCurlTransport(impersonate="chrome")
class Plain:
    def __init__(self):
        self.h = {"User-Agent": "Mozilla/5.0"}
