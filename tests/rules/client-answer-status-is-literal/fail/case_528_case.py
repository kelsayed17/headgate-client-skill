class C:
    def s(self, s):
        return _responses.Expect(decoder(A), {404: decoder(B), s: decoder(D)})
