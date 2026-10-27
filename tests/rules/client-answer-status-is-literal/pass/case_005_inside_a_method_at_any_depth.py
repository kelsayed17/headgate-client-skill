# Inside a method at any depth: a closure, a lambda, a decorated or async method, a class nested in a function.
class C:
    def m(self):
        def build():
            return Expect(decoder(A)).on(404, decoder(B))
        return build

    def n(self):
        return lambda: Expect(decoder(A), {404: decoder(B)})

    @staticmethod
    def s():
        return Expect(decoder(A)).on(404, decoder(B))

def factory():
    class Inner:
        async def m(self):
            return Expect(decoder(A)).on(404, decoder(B))
    return Inner
