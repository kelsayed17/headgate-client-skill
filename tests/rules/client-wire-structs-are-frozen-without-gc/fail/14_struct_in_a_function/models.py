def build():
    class Inner(msgspec.Struct, gc=False):
        x: int

    return Inner
