# The same case with its readers moved to module level (R3).
A = decoder(A)


Loose = dict


class C(AsyncBaseClient):
    async def get_a(self) -> Loose:
        return await self.get("a", expect=A)
