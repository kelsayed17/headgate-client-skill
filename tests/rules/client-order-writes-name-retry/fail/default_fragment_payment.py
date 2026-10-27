class Bank(AsyncBaseClient):
    async def send_payment(self, payment: NewPayment) -> Payment:
        return await self.post("payments", body=NEW_PAYMENT(payment), expect=PAYMENT)
