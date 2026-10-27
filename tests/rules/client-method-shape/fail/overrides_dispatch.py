# Overriding any of headgate 0.7.0's own request machinery reshapes every call behind the one-statement bodies.
class C(AsyncBaseClient):
    def _dispatch(self, resp: Response, spec: Expect[T], site: CallSite) -> T:
        return super()._dispatch(resp, spec, site)
