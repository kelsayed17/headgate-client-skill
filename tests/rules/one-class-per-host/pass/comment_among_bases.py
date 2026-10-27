# A comment inside the bases list is not a base: the class subclasses AsyncBaseClient alone.
from headgate import AsyncBaseClient

API = "https://api.example"


class Client(
    AsyncBaseClient,  # the one base
    # nothing else
):
    def __init__(self) -> None:
        super().__init__(base_url=API)
