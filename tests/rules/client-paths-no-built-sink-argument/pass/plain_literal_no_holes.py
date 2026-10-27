async def get_clock(self) -> Clock:
    return await self.get("/v2/clock", expect=CLOCK)

def list_orders(self):
    return self.paginate("/v2/orders", expect=ORDERS, pages=PAGER, limit=LIMIT)
