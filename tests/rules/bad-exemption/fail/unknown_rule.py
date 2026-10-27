"""An allow comment naming a rule that does not exist."""

from headgate import AsyncBaseClient


class ExampleClient(AsyncBaseClient):  # headgate-verify: allow no-such-rule -- a reason
    """The client."""
