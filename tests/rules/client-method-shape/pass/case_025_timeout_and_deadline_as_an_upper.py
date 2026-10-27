# timeout= and deadline= as an UPPER_CASE module constant, public or private: a value fixed at import, never one
# computed per call (paper.clients._retry's LONG_READ and LONG_READ_DEADLINE, since headgate 0.3.0).
class Slow(AsyncBaseClient):
    async def fetch_file(self) -> bytes:
        return await self.get("file.zip", expect=as_bytes, timeout=LONG_READ, deadline=LONG_READ_DEADLINE)

    async def fetch_other(self, **params: Unpack[OtherParams]) -> bytes:
        return await self.get("other.zip", params=params, expect=as_bytes, timeout=_READ, deadline=_DEADLINE_2)
