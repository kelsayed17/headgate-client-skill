class C(AsyncBaseClient):
    async def get_account(self, user_id: UUID) -> Account:
        return await self.get("account", headers=self._user_headers(user_id), expect=decoder(Account))
