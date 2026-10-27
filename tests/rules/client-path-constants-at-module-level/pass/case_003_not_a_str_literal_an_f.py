# Not a str literal: an f-, t- or bytes string, a name, a call.
class C:
    A_PATH = f"/a/{X}"
    B_PATH = t"/b"
    C_PATH = b"/c"
    D_PATH = _MODULE_PATH
    E_PATH = make_path()
    F_PATH = ("/f/" f"{y}")
    G_PATH = (b"/g/" b"h")
