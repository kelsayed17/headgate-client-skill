def _t():
    return AsyncCurlTransport(impersonate="chrome")
class Imp:
    def __init__(self):
        _t()
class Plain:
    def __init__(self, ua):
        self.h = {"User-Agent": ua}
