# A comment where the first or second argument would be is not that argument; a method whose name only CONTAINS
# `on` is not `.on`.
class C:
    def m(self, strict, handler):
        self.on_close(handler)
        resp.json(strict)
        return Expect(
            # the 200 body
            decoder(A),
            {404: decoder(B)},
        )
