# headgate's deadline= is a knob like the others: a computed value is reported (a module constant is not since
# 2026-10-26; see the valid `Slow` case).
class C(AsyncBaseClient):
    async def fetch_x(self, size: int) -> bytes:
        return await self.get("x", expect=as_bytes, deadline=_deadline_for(size))
