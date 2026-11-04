# A public delegate over a private raw leg: the leg may return bytes, the public method may not.
class C(AsyncBaseClient):
    async def get_report(self) -> bytes:
        return await self._raw("report")

    async def _raw(self, path: str) -> bytes:
        return await self.get(path, expect=as_bytes)
