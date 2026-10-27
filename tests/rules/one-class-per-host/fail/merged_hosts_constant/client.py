# The second host hidden in a module constant passed to a verb.
from headgate import AsyncBaseClient, Rate

API = "https://api.one.example"
SERIES_URL = "https://data.two.example/series"
RATE = Rate(5)


class Client(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=API, rate=RATE)

    def get_series(self) -> Paginated[SeriesPage, Series]:
        return self.paginate(SERIES_URL, expect=SERIES_PAGE, pages=SERIES_PAGES, limit=MAX_PAGES)
