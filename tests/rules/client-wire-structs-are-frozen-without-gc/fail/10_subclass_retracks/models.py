class Page(msgspec.Struct, frozen=True, gc=False):
    cursor: str | None = None


class TradesPage(Page, gc=True):
    trades: list[str] = []
