class AccountsPage(Page):
    @property
    def total(self) -> int:
        return len(self.items)
