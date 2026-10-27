# Out of scope: properties, private helpers, lifecycle, dunders, and a sync or async private method.
class BlsClient(AsyncBaseClient):
    @property
    def max_years_per_request(self) -> int:
        """20 with a registered key, 10 without."""
        return 20 if self._api_key else 10

    @property
    def staleness_hours(self) -> float | None:
        if self._last_success is None:
            return None
        return (time.time() - self._last_success) / 3600

    @staticmethod
    def _uid(user_id: UUID) -> dict[str, str]:
        return {"X-Internal-User-Id": str(user_id)}

    async def _token(self) -> str:
        if self._guest_token is None:
            minted = await self.mint_guest_token()
            self._guest_token = minted.guest_token
        return self._guest_token

    async def aclose(self) -> None:
        await self._other.aclose()
        await super().aclose()

    async def __aenter__(self) -> Self:
        return self
