# Not a pathy FIRST target: another name, a later target of a chain, a tuple, an attribute.
class C:
    TIMEOUT = "30"
    A = B_PATH = "/b"
    C_PATH, D = "/c", "d"
    (E_PATH, F) = ("/e", "f")
    (G_PATH,) = "g"
    H_PATH, = "h"
