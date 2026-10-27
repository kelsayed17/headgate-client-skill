transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)
_OPTIONS = headgate.HttpOptions(transport=transport, user_agent=_PRODUCT_TOKEN)
