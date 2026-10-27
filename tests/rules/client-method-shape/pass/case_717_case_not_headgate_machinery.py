# An in-tree base's old request-method name means nothing to headgate 0.7.0: defining it is a private helper.
class C(AsyncBaseClient):
    def _status_error(self, resp: Any, url: str) -> Any:
        return None
