def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


@uses(_t())
class C:
    HEADERS = {"User-Agent": "x"}
