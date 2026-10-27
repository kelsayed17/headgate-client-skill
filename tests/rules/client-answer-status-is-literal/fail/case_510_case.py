class C:
    async def n(self, s):
        return await self.get("x", expect=Expect(decoder(A)).on(status=s, read=decoder(B)))
