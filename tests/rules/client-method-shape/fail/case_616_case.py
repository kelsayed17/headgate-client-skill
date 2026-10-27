from paper.clients.public.client import PublicClient


class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class Sub(PublicClient):
    _BASE: ClassVar[str] = _OTHER
