"""Mozilla/5.0 is what this module sends."""

transport = AsyncCurlTransport(impersonate="chrome", default_headers=True)
