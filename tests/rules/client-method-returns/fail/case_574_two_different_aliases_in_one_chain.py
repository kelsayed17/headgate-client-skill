# Two DIFFERENT aliases in one chain: rejected (the metavariable binds once), loudly.
_A = decoder(A)
_NOT_FOUND = decoder(NotFound)


class C(AsyncBaseClient):
    async def get_x(self) -> A | NotFound:
        return await self.get("x", expect=Expect(_A).on(404, _NOT_FOUND))
