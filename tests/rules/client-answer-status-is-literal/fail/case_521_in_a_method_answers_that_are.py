# In a method, answers that are not a dict literal with int keys: a name, a keyword name, a call, a comprehension,
# a spread, a non-literal key, a starred second argument; through every spelling of Expect.
class C:
    async def r(self, answers):
        return await self.get("x", expect=Expect(decoder(A), answers))
