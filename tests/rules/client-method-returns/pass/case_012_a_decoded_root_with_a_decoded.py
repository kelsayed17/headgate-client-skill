# A decoded root with a decoded answer; `as_bytes` with a decoded answer and a reader function; a bare reader
# function; chained answers; decoder aliases as root and as answer. The success type is the FIRST union arm.
_NOT_FOUND = decoder(NotFound)
_ROWS = decoder(list[Row])


def _not_published(resp: httpx2.Response, /) -> NotPublished:
    return NotPublished()


def _placed_or_declined(resp: httpx2.Response, /) -> PaperOrder | Declined:
    return Declined()


class Answers(AsyncBaseClient):
    async def close_position_by_id(self, user_id: UUID, position_id: str) -> PaperPositionClose | PositionNotFound:
        return await self.post(
            t"/api/brokerage/positions/{position_id}/close",
            headers=self._uid(user_id),
            retry=False,
            expect=Expect(decoder(PaperPositionClose)).on(404, decoder(PositionNotFound)),
        )

    async def fetch_answer(self, domain: str, *, body: Any | None = None) -> bytes | NotInHistory:
        return await self.post(t"/internal/history/{domain}", json=body, expect=Expect(as_bytes).on(404, decoder(NotInHistory)))

    async def preflight_single_leg(self, account_id: str, body: PreflightBody) -> Preflight | PreflightRejection:
        return await self.post(t"/preflight/{account_id}", json=to_builtins(body), expect=Expect(decoder(Preflight)).on(400, decoder(PreflightRejection)))

    async def fetch_cnsfails(self, year: int) -> bytes | NotPublished:
        return await self.get(t"files/cnsfails{year:04d}.zip", expect=Expect(as_bytes).on(404, _not_published), timeout=60)

    async def place_option_order(self, request: OptionOrderRequest) -> PaperOrder | Declined:
        return await self.post("/orders", json=to_builtins(request), retry=False, expect=_placed_or_declined)

    async def get_order(self, order_id: str) -> Order | NotFound | Gone:
        return await self.get(t"/orders/{order_id}", expect=Expect(decoder(Order)).on(404, decoder(NotFound)).on(410, decoder(Gone)))

    async def get_rows(self) -> list[Row] | NotFound:
        return await self.get("/rows", expect=Expect(_ROWS).on(404, decoder(NotFound)))

    async def get_one(self, row_id: str) -> Row | NotFound:
        return await self.get(t"/rows/{row_id}", expect=Expect(decoder(Row)).on(404, _NOT_FOUND))
