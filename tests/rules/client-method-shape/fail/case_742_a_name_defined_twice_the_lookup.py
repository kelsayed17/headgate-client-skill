# A name defined twice: the lookup would read the first while the runtime runs the second (ruff's F811 skips
# `_` names, measured). A class method twice, a decorated duplicate, a method rebound to an UPPER name, a
# module leg twice.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def _leg(self, path: str) -> A:
        return await self.get(path, expect=A)

    async def _leg(self, path: str) -> A:
        a = await self.get(path, expect=A)
        return a.x

    async def get_a(self) -> A:
        return await self._leg("/a")
