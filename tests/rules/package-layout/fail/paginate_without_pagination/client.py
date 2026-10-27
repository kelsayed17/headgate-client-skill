from headgate import AsyncBaseClient, Rate

ITEM_PAGES = NextUrl(items=_items, next=_next)
MAX_PAGES = PageLimit(20)

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    def get_items(self) -> Paginated[ItemPage, Item]:
        return self.paginate("items", expect=ITEM_PAGE, pages=ITEM_PAGES, limit=MAX_PAGES)
