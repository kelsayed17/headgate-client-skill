# #1401's test_a_documented_answer_marker_does_not_change_the_wire_shape, the passing half: the marker after
# the raw arm still reads raw.
# The same case with its readers moved to module level (R3).
AS_BYTES_404_NOT_PUBLISHED = Expect(as_bytes).on(404, decoder(NotPublished))


class C(AsyncBaseClient):
    async def fetch_a(self) -> bytes | NotPublished:
        return await self.get("a", expect=AS_BYTES_404_NOT_PUBLISHED)
