class C:
    async def s(self, s):
        return await self.get("x", expect=Expect(decoder(A), answers={s: decoder(B)}))
