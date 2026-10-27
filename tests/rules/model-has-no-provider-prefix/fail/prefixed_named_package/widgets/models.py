import msgspec


class WidgetsParamsPage(msgspec.Struct, frozen=True):
    page: int
