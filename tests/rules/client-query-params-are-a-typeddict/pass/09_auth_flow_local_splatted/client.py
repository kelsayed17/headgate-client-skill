class Auth:
    async def _mint(self) -> str:
        params: TokenParams = {"grant_type": "refresh_token"}
        params["client_secret"] = self._secret
        async with OAuthClient() as oauth:
            token = await oauth.refresh_access_token(**params)
        return token.access_token
