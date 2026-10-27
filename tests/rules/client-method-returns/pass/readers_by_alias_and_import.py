# A reader function named by an UPPER_CASE alias, and a reader imported from another module (its type is not
# visible here, so it is taken on trust: disclosed in the rule).
from .readers import ORDER_PAGE


def _placed_or_declined(resp: httpx2.Response, /) -> Order | Declined:
    return Declined()


PLACED_OR_DECLINED = _placed_or_declined


class C(AsyncBaseClient):
    async def place_order(self, order: NewOrder) -> Order | Declined:
        return await self.post("orders", body=NEW_ORDER(order), retry=False, expect=PLACED_OR_DECLINED)

    async def get_orders(self) -> OrderPage:
        return await self.get("orders", expect=ORDER_PAGE)
