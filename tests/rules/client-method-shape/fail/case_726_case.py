class C(AsyncBaseClient):
    def __new__(cls) -> Self:
        return object.__new__(cls)
