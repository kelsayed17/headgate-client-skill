class TruthSocialClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(
            base_url=_BASE_URL,
            http=HttpOptions(
                transport=AsyncCurlTransport(impersonate="chrome", default_headers=True),
                user_agent="acme/1.0",
            ),
        )
