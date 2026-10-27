def _chrome_transport() -> httpx2.AsyncBaseTransport:
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class YahooQueryClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_QUERY_BASE_URL, http=HttpOptions(transport=_chrome_transport()))


class YahooWsClient(AsyncBaseClient):
    def __init__(self, user_agent: str) -> None:
        super().__init__(
            base_url=_WS_BASE_URL,
            http=HttpOptions(headers={"User-Agent": user_agent, "Accept": "application/json"}),
        )


class YahooWsProductClient(AsyncBaseClient):
    def __init__(self, user_agent: str) -> None:
        super().__init__(base_url=_WS_BASE_URL, http=HttpOptions(user_agent=user_agent))
