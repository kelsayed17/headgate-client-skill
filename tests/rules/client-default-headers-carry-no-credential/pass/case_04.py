AsyncCurlTransport(impersonate="chrome", default_headers=True)


class HttpOptions:
    headers: Mapping[str, str] = field(default_factory=dict)


def build(headers: dict[str, str]) -> HttpOptions:
    return HttpOptions(headers=headers)
