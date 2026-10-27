# A walk: a sync def whose one statement returns headgate's lazy `self.paginate(...)`, its pager and page budget
# module constants (headgate 0.4.0; coin_metrics' walk_asset_metrics, 2026-10-26).
# Readers moved to module level (R3); `limit=` is required here (the spec passes a PageLimit).
X_PAGE = decoder(XPage)
Y_PAGE = decoder(YPage)


class Walks(AsyncBaseClient):
    def walk_x(self, **params: Unpack[XParams]) -> Paginated[XPage, XRow]:
        """Every page, lazily."""
        return self.paginate("x", params=params, expect=X_PAGE, pages=X_PAGES, limit=PAGE_LIMIT)

    def walk_y(self) -> Paginated[YPage, YRow]:
        return self.paginate("y", expect=Y_PAGE, pages=_Y_PAGES, limit=_Y_LIMIT, timeout=LONG_READ)
