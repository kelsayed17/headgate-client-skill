class Params(TypedDict, total=False):
    symbol: str


class Unrelated(Base):
    pass


class StructLike(MyStruct):
    pass
