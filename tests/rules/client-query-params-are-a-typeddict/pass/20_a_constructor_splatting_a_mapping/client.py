class Auth:
    def _token(self, payload: dict[str, str]) -> Token:
        return Token(**payload)
