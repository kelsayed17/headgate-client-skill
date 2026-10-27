import string.templatelib
import string.templatelib as tl

def f(x: object) -> bool:
    return isinstance(x, Template) or isinstance(x, tl.Template)
