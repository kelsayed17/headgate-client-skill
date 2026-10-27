class C:
    @functools.cache
    def p(self) -> Template:
        return Template(self._frag)
