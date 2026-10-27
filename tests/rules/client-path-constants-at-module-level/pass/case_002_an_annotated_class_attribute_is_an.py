# An ANNOTATED class attribute is an AnnAssign, which the test did not read.
class C(AsyncBaseClient):
    _BASE_URL: ClassVar[str] = "https://api.example.org"
