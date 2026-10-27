class Client(AsyncBaseClient):
    @classmethod
    def build(cls, *, user_agent: str = _UA) -> Client:
        return cls(user_agent=user_agent)
