# #1401's documented-answer forms: a one-argument Expect root and `.on(...)`, and a module reader function.
# R3: the source's inline reader; `expect=` is a module-level name here.
def _not_published(resp: httpx.Response, /) -> NotPublished:
    return NotPublished()


def _placed_or_declined(resp: httpx.Response, /) -> PaperOrder | Declined:
    return Declined()


class Answers(AsyncBaseClient):
    async def close_position_by_id(self, user_id: UUID, position_id: str) -> PaperPositionClose | PositionNotFound:
        return await self.post(
            t"/api/brokerage/positions/{position_id}/close",
            headers=self._uid(user_id),
            retry=False,
            expect=Expect(decoder(PaperPositionClose)).on(404, decoder(PositionNotFound)),
        )

    async def answer(self, domain: str, *, body: Any | None = None) -> bytes | NotInHistory:
        return await self.post(t"/internal/history/{domain}", json=body, expect=Expect(as_bytes).on(404, decoder(NotInHistory)))

    async def fetch_cnsfails(self, year: int) -> bytes | NotPublished:
        return await self.get(t"files/cnsfails{year:04d}.zip", expect=Expect(as_bytes).on(404, _not_published), timeout=LONG_READ)

    async def place_option_order(self, user_id: UUID, request: OptionOrderRequest) -> PaperOrder | Declined:
        return await self.post("/orders", body=_WRITE(request), retry=False, expect=_placed_or_declined)
