def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


def headers():
    return {"User-Agent": "x"}
