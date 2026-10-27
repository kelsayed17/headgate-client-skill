# Out of scope: properties, private helpers, dunders, non-transport classes.
class SenateEFDClient(AsyncBaseClient):
    @property
    def staleness_hours(self) -> float | None:
        return None

    @property
    def headers(self) -> dict[str, str]:
        return {}

    async def _token(self) -> str | None:
        return self._guest_token

    @staticmethod
    def _uid(user_id: UUID) -> dict[str, str]:
        return {"X-Internal-User-Id": str(user_id)}


class AsgiApp(Protocol):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None: ...


class FinraOAuth(httpx2.Auth):
    async def get_token(self) -> str | None:
        return self._token
