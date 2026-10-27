# The default fragments (order, orders, transfer, withdraw, payment): each write names retry=.
class Bank(AsyncBaseClient):
    async def create_transfer(self, transfer: NewTransfer) -> Transfer:
        return await self.post("transfers", body=NEW_TRANSFER(transfer), expect=TRANSFER, retry=False)

    async def withdraw_funds(self, request: Withdrawal) -> Receipt:
        return await self.post("withdrawals", body=WITHDRAWAL(request), expect=RECEIPT, retry=False)

    async def update_profile(self, profile: Profile) -> Profile:
        return await self.put("profile", body=PROFILE_WRITER(profile), expect=PROFILE)

    async def get_orders(self) -> OrderPage:
        return await self.get("orders", expect=ORDER_PAGE)
