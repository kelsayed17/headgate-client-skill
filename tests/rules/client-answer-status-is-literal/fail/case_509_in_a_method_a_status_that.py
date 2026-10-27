# In a method, a status that is not an int literal: a name, a keyword name, a bool, a negative, a float, a
# string, a complex, a starred argument, an expression in parentheses.
class C:
    async def n(self, s):
        return await self.get("x", expect=Expect(decoder(A)).on(s, decoder(B)))
