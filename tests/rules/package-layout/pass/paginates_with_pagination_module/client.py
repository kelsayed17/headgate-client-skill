from headgate import AsyncBaseClient, Rate

from .pagination import ITEM_PAGES, MAX_PAGES

API = "https://api.one.example"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    def get_items(self) -> Paginated[ItemPage, Item]:
        return self.paginate("items", expect=ITEM_PAGE, pages=ITEM_PAGES, limit=MAX_PAGES)
