# A raw arm after a model arm is still a raw return: every arm is read, not only the first.
class C(AsyncBaseClient):
    async def get_cnsfails(self, year: int) -> NotPublished | bytes:
        return await self.get(t"files/cnsfails{year:04d}.zip", expect=Expect(decoder(NotPublished)).on(404, decoder(NotPublished)))
