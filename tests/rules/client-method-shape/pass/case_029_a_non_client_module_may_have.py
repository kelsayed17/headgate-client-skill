# A non-client module may have call defaults and a name bound twice (typing overloads).
@overload
def _pick(x: int) -> int: ...
@overload
def _pick(x: str) -> str: ...
def _pick(x, *, sentinel=_Sentinel()):
    return x
