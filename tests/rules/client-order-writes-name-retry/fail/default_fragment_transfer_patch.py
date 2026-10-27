class Bank(AsyncBaseClient):
    async def amend_transfer(self, transfer_id: str, change: TransferChange) -> Transfer:
        return await self.patch(t"transfers/{transfer_id}", body=CHANGE(change), expect=TRANSFER)
