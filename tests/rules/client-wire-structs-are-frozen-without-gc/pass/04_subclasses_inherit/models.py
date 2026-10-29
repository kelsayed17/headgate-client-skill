class Page(msgspec.Struct, frozen=True, gc=False):
    cursor: str | None = None


class TradesPage(Page):
    trades: list[str] = []


class StrictTradesPage(Page, forbid_unknown_fields=True):
    trades: list[str] = []


class TradesEnvelope(Envelope[Trade]):
    pass
