# I4: AsyncBaseClient under another name.
# Readers moved to module level (R3).
A = decoder(A)


from headgate import AsyncBaseClient as _Transport


class C(_Transport):
    async def get_a(self) -> A:
        x = await self.get("a", expect=A)
        return x
