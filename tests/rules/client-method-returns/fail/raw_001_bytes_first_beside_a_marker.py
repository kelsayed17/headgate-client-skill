# The source's own accepted raw shape, `bytes | NotPublished`: a raw first arm beside a documented marker.
class C(AsyncBaseClient):
    async def get_cnsfails(self, year: int) -> bytes | NotPublished:
        return await self.get(t"files/cnsfails{year:04d}.zip", expect=Expect(as_bytes).on(404, decoder(NotPublished)))
