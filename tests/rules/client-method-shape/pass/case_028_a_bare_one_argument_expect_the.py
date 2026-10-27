# A bare one-argument Expect; the request keywords content=/files=/idempotency_key=; a None knob (headgate's
# `deadline=None`, the bulk-file shape until headgate 0.3.0); an untyped knob
# default; a property reading a sub-object's attribute that shares a private method's name; an unrelated
# aliased import.
# Readers moved to module level (R3).
X = Expect(decoder(X))
ACK = decoder(Ack)
Z = decoder(Z)
INT = decoder(int)


import datetime as dt


class More(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)

    async def upload(self, blob: bytes, files: Files, idempotency_key: str) -> Ack:
        return await self.post("up", content=blob, files=files, idempotency_key=idempotency_key, expect=ACK)

    async def fetch_bulk(self) -> bytes:
        return await self.get("bulk.zip", expect=as_bytes, timeout=LONG_READ, deadline=None)

    async def get_z(self, timeout=30.0) -> Z:
        return await self.get("z", timeout=timeout, expect=Z)

    @property
    def count(self) -> int:
        return self._state._count

    async def _count(self) -> int:
        return await self.get("count", expect=INT)
