import os
x = 1

@functools.cache
def p(s: str) -> str:
    return f"/a/{s}"
