class FarsideClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            http=HttpOptions(transport=AsyncCurlTransport(impersonate="chrome", curl_options={CurlOpt.FRESH_CONNECT: True})),
        )
