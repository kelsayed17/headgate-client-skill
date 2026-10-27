# headgate's other request internals (PAPER-574.6): the streamed send, the exchange, the sent hook.
class C(AsyncBaseClient):
    def _streamed(self, call: Any) -> Any:
        return super()._streamed(call)
