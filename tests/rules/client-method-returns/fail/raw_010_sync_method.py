# A sync public method is read too.
class C(AsyncBaseClient):
    def get_report(self) -> bytes:
        return self.get_sync("report", expect=as_bytes)
