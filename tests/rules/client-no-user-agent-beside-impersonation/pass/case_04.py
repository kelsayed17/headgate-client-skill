def _t():
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class Imp:
    def __init__(self):
        _t()

    class Headers:
        DEFAULT = {"User-Agent": "acme"}


class Builder:
    def _build(self):
        return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class Plain:
    def __init__(self, ua):
        self._build()
        self.h = {"User-Agent": ua}


NAMES = ("user-agent", "X-User-Agent", "User-Agent: x", "User-Agents")
NOTE = "send Mozilla/5.0 here"
PAIR = "User-" "Agents"
