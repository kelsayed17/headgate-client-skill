def _chrome_transport() -> httpx2.AsyncBaseTransport:
    return AsyncCurlTransport(impersonate="chrome", default_headers=True)


class YahooQueryClient(AsyncBaseClient):
    def __init__(self, user_agent: str) -> None:
        super().__init__(http=HttpOptions(transport=_chrome_transport(), user_agent=user_agent))
