import os

@functools.cache
def _p(v: str, spec: str) -> Template:
    x = 1
    return t"/x/{v:{spec}}"
