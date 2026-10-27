def _t():
    return AsyncCurlTransport(impersonate="chrome")
class C:
    def __init__(self):
        _t()
        self.h = {'User-Agent': 'x'}
