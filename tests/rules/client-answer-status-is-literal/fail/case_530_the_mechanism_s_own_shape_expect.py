# The mechanism's own shape: Expect.on rebuilding its widened copy. On the real tree it carries an inline
# suppression; `ast-grep test` ignores those, so here it is reported.
class Expect:
    def on(self, status, read):
        widened = {**self.answers, status: read}
        return Expect(self.ok, widened)
