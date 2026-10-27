class C:
    @property
    def p(self) -> str:
        def inner() -> str:
            feed_url = "feeds/x.xml"
            return feed_url
        return inner()
