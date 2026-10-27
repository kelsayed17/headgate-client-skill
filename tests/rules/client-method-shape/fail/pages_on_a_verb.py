# `pages=` and `limit=` are paginate's; no verb takes them.
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X, pages=X_PAGES, limit=MAX_PAGES)
