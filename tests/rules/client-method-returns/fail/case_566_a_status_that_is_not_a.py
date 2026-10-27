# A status that is not a literal integer; three arguments; a keyword or dict answer table; an accept= or headers=;
# an Expect that is not the house one; a chain on something else.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(decoder(X)).on(NOT_FOUND, decoder(NotFound)))
