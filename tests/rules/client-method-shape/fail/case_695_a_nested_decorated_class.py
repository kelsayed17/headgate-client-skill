# A nested decorated class.
class C(AsyncBaseClient):
    @dataclass
    class Endpoints:
        x: str = "x"
