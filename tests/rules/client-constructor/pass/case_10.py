class _TokenAuth(httpx2.Auth):
    def __init__(self, token: str) -> None:
        self._token = token
