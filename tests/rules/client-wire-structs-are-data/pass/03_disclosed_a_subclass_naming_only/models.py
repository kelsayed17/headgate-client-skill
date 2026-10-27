class AccountsPage(Page):
    @property
    def total(self) -> int:
        return len(self.items)


class Quote(msgspec.Struct):
    mid = property(lambda self: (self.bid + self.ask) / 2)
