import os

class C:
    @property
    def p(self) -> str:
        x = 1
        return _BARS_PATH.format(x)
