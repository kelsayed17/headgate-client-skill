# I5: a property publishing a method, and a dunder that could synthesize endpoints.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    @property
    def get_total(self) -> Any:
        return self._get_total

    async def _get_total(self, a: str) -> int:
        x = await self.get(t"/a/{a}", expect=A)
        return x.n
