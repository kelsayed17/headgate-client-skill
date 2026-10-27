# An in-tree base's old request-method name means nothing to headgate 0.7.0: defining it is a private helper.
# Defining _fetch or _client_error (the base's names until 2026-09-29, still refused).
class C(AsyncBaseClient):
    async def _fetch(self, *args: Any, **kwargs: Any) -> Any:
        return None
