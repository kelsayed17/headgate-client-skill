# A knob valued with a name that appears only in a type annotation, not as a parameter.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, wait: Seconds) -> A:
        return await self.get("/a", timeout=Seconds, expect=A)
