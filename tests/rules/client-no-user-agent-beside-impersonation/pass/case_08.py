transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)
identity = Identity(user_agent="acme")
HttpOptions(transport=transport, headers={"Accept": "*/*"})
