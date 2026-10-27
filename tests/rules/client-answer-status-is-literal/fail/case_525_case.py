class C:
    def r(self, more):
        return Expect(decoder(A), {404: decoder(B), **more})
