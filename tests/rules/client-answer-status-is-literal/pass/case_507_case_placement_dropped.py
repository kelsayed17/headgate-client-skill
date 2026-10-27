# Placement no longer matters (answers are declared at module level); the status is a literal, so this passes.
class C:
    build = lambda self: Expect(decoder(A)).on(404, decoder(B))
