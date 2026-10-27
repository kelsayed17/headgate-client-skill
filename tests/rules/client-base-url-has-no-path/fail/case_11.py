_BASE_URL = "https://api.finra.org/data/group"

class FinraClient(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url=_BASE_URL)
