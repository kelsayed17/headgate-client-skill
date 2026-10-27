# headgate-verify: allow client-module-has-a-client -- nothing here is reported
"""An allow comment over a module that already has its client."""

from headgate import AsyncBaseClient


class ExampleClient(AsyncBaseClient):
    """The client."""
