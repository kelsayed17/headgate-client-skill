def _chrome_transport() -> httpx2.AsyncBaseTransport:
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class TruthSocialClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            http=HttpOptions(transport=AsyncCurlTransport(impersonate=_IMPERSONATE, default_headers=True)),
        )


class NyseClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            http=HttpOptions(
                transport=AsyncCurlTransport(
                    impersonate="chrome", default_headers=True, curl_options={CurlOpt.FRESH_CONNECT: True}
                ),
            ),
        )


transport = curl.AsyncCurlTransport(default_headers=(True), impersonate="chrome")
doubled = AsyncCurlTransport(impersonate="chrome", default_headers=((True)))
