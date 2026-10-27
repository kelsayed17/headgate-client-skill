class C(AsyncBaseClient):
    def __init__(self) -> None:
        super().__init__(base_url="https://feeds.bbci.co.uk/news")
