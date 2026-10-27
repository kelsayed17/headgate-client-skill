# extensions= is no longer a keyword of any verb: a parameter and a dict literal are both reported.
class C(AsyncBaseClient):
    async def fetch_x(self, ext: dict[str, float]) -> bytes:
        return await self.get("x", extensions=ext, expect=as_bytes)
