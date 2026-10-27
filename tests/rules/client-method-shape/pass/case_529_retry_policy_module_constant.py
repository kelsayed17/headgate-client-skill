# R10: `retry=` may name a module-level policy, an UPPER_CASE name the module binds (the source banned this case).
from headgate import RetryPolicy

from .policies import RETRY_EVERY_METHOD

ORDER = decoder(Order)
ORDER_RETRY = RetryPolicy(attempts=1)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.post("x", expect=as_bytes, retry=RETRY_EVERY_METHOD)

    async def place_order(self, order: NewOrder) -> Order:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER, retry=ORDER_RETRY)
