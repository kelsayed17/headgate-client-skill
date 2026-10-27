# Minor: a class-level value is an UPPER_CASE name: not a literal host, not a rebind of a leg.
class C(AsyncBaseClient):
    _BASE = "https://literal.example"
