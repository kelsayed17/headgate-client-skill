class C:
    async def m(self):
        return await self.get(
            "x",
            expect=Expect(decoder(A)).on(
                # Public's documented 400
                400,
                decoder(B),
            ),
        )
