# R3: a hand-written reader function the module defines is passed by its own name.
def _placed_or_declined(resp: httpx2.Response, /) -> Order | Declined:
    return Declined()


class Answers(AsyncBaseClient):
    async def place_option_order(self, request: OptionOrderRequest) -> Order | Declined:
        return await self.post("/orders", body=_WRITE(request), retry=False, expect=_placed_or_declined)
