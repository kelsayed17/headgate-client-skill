# A chain's status is an int literal or an HTTPStatus member.
X_OR_GONE = Expect(decoder(X)).on(GONE, decoder(Gone))


class C(AsyncBaseClient):
    async def get_x(self) -> X | Gone:
        return await self.get("x", expect=X_OR_GONE)
