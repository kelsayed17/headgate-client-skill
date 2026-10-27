# A keyword whose NAME is a parameter forwarding a global: the keyword name is not the value.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, data: Form) -> X:
        return await self.post("x", data=_FORM, expect=X)
