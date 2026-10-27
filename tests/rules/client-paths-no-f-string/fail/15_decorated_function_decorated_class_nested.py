class C:
    def m(self) -> None:
        def inner() -> None:
            y = 2
            return self.get(f"/a/{y}")
