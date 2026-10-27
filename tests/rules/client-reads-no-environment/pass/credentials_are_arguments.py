import os
from pathlib import Path


class FredClient(AsyncBaseClient):
    def __init__(self, *, api_key: str) -> None:
        super().__init__(base_url=_BASE_URL, auth=QueryParamAuth({"api_key": api_key}))


CACHE = Path(os.sep) / "tmp"
NOTE = "set os.environ['FRED_KEY'] before calling"
env = settings.environ
reader = other.getenv("X")
"""os.getenv is how a caller supplies the key; the client takes it as an argument."""
