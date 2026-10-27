# A walk that is not the plain shape: async (it would hand back a coroutine), awaited, built or bound at the call,
# a pager or budget that is not a module constant, a body (pages are GETs), two statements, a method chained on the
# walk, a decorated walk.
# Readers moved to module level (R3).
X_PAGE = decoder(XPage)


class C(AsyncBaseClient):
    async def walk_x(self, **params: Unpack[XParams]) -> Paginated[XPage, XRow]:
        return self.paginate("x", params=params, expect=X_PAGE, pages=X_PAGES)
