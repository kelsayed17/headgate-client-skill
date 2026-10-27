class C:
    async def r(self, answers):
        return await self.get("x", expect=Expect(decoder(A), answers=answers))
