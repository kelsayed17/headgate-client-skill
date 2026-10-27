# #1401's documented-answer forms: a one-argument Expect root and `.on(...)`, and a module reader function.
# Readers moved to module level (R3); a reader function is named by an UPPER_CASE module alias.
PAPER_POSITION_CLOSE_404_POSITION_NOT_FOUND = Expect(decoder(PaperPositionClose)).on(404, decoder(PositionNotFound))
AS_BYTES_404_NOT_IN_HISTORY = Expect(as_bytes).on(404, decoder(NotInHistory))
AS_BYTES_404_NOT_PUBLISHED = Expect(as_bytes).on(404, _not_published)


def _not_published(resp: httpx.Response, /) -> NotPublished:
    return NotPublished()


def _placed_or_declined(resp: httpx.Response, /) -> PaperOrder | Declined:
    return Declined()


PLACED_OR_DECLINED = _placed_or_declined


class Answers(AsyncBaseClient):
    async def close_position_by_id(self, user_id: UUID, position_id: str) -> PaperPositionClose | PositionNotFound:
        return await self.post(
            t"/api/brokerage/positions/{position_id}/close",
            headers=self._uid(user_id),
            retry=False,
            expect=PAPER_POSITION_CLOSE_404_POSITION_NOT_FOUND,
        )

    async def answer(self, domain: str, *, body: Any | None = None) -> bytes | NotInHistory:
        return await self.post(t"/internal/history/{domain}", json=body, expect=AS_BYTES_404_NOT_IN_HISTORY)

    async def fetch_cnsfails(self, year: int) -> bytes | NotPublished:
        return await self.get(t"files/cnsfails{year:04d}.zip", expect=AS_BYTES_404_NOT_PUBLISHED, timeout=LONG_READ)

    async def place_option_order(self, user_id: UUID, request: OptionOrderRequest) -> PaperOrder | Declined:
        return await self.post("/orders", body=_WRITE(request), retry=False, expect=PLACED_OR_DECLINED)
