import msgspec


class Filing(msgspec.Struct, frozen=True):
    id: str


class FilingPage(msgspec.Struct, frozen=True):
    results: list[Filing]
