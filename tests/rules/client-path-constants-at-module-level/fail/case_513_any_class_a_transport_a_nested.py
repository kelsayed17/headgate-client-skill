# Any class: a transport, a nested class, a class in a function, a decorated class, a one-line class.
class C(AsyncBaseClient):
    """A client."""

    TIMEOUT = 30
    ORDERS_PATH = "/orders"

    def __init__(self) -> None: ...
