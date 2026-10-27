# R3: a reader function named directly is a lowercase name; bind it to an UPPER_CASE module name.
def _placed_or_declined(resp: httpx2.Response, /) -> Order | Declined:
    return Declined()


class Answers(AsyncBaseClient):
    async def place_option_order(self, request: OptionOrderRequest) -> Order | Declined:
        return await self.post("/orders", body=_WRITE(request), retry=False, expect=_placed_or_declined)
