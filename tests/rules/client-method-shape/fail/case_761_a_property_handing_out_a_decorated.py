# A property handing out a DECORATED method.
class C(AsyncBaseClient):
    @property
    def total(self) -> Any:
        return self._total

    @staticmethod
    async def _total() -> int:
        return 1
