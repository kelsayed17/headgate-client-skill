# Both spellings, in a method, with an int literal: positional, keyword, the constructor's dict positional or
# keyword; chained `.on`s; hex; parenthesised.
class C:
    async def m(self):
        return await self.get("x", expect=Expect(decoder(A)).on(400, decoder(B)))

    async def p(self):
        return await self.get("x", expect=Expect(decoder(A), {403: decoder(B)}))

    async def q(self):
        return await self.get("x", expect=Expect(ok=decoder(A), answers={404: decoder(B), 409: decoder(D)}))

    async def t(self):
        return await self.get("x", expect=Expect(decoder(A)).on(status=410, read=decoder(B)))

    async def chained(self):
        return await self.get("x", expect=Expect(_fd_index).on(304, _fd_index).on(404, _fd_index))

    async def hexed(self):
        return await self.get("x", expect=_responses.Expect[T](decoder(A), {0x194: decoder(B)}).on((409), r))

    async def empty(self):
        return await self.get("x", expect=Expect(decoder(A), {}))

    async def parenthesised(self):
        return await self.get("x", expect=Expect(decoder(A), {(404): decoder(B)}))
