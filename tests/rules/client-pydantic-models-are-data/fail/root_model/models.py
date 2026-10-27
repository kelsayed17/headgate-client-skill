class Prices(RootModel[list[float]]):
    def total(self) -> float:
        return sum(self.root)
