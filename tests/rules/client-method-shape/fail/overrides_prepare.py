class C(AsyncBaseClient):
    def _prepare(self, call: Call) -> Prepared:
        return super()._prepare(call)
