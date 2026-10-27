# A walk: a sync def whose one statement returns headgate's lazy `self.paginate(...)`, its pager and page budget
# module constants (headgate 0.4.0; coin_metrics' walk_asset_metrics, 2026-10-26).
# R3: the source's inline reader; `expect=` is a module-level name here.
class Walks(AsyncBaseClient):
    def walk_x(self, **params: Unpack[XParams]) -> Paginated[XPage, XRow]:
        """Every page, lazily."""
        return self.paginate("x", params=params, expect=decoder(XPage), pages=X_PAGES, limit=PAGE_LIMIT)

    def walk_y(self) -> Paginated[YPage, YRow]:
        return self.paginate("y", expect=decoder(YPage), pages=_Y_PAGES, timeout=LONG_READ)
