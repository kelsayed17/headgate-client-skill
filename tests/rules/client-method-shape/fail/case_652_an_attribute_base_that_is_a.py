# An attribute base that is a public client; a sync decorated public method that calls nothing.
class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class Sub(public.PublicClient):
    _BASE: ClassVar[str] = _OTHER
