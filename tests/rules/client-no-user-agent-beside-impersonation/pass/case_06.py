def _headers():
    return {}


@functools.cache
def _defaults():
    return {}


@functools.cache
def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class _Session:
    transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)


@final
class _Pool:
    transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)


class Plain:
    def __init__(self, ua):
        _headers()
        _defaults()
        _Session()
        _Pool()
        self.h = {"User-Agent": ua}


@final
class Marked:
    HEADERS = {"User-Agent": "acme"}
