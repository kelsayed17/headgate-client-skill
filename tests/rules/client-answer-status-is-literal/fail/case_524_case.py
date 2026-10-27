class C:
    def r(self, codes):
        return Expect(decoder(A), {c: decoder(B) for c in codes})
