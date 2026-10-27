# Readers moved to module level (R3).
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    async def walk_x(self, **params: Unpack[XParams]) -> Paginated[XPage, XRow]:
        return await self.paginate("x", params=params, expect=X_PAGE, pages=X_PAGES)
