def factory() -> type:
    class Inner(AsyncBaseClient):
        def __init__(self, *, user_agent: str = _UA) -> None:
            pass

    return Inner
