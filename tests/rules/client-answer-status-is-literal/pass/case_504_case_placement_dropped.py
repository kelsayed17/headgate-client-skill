# Placement no longer matters (answers are declared at module level); the status is a literal, so this passes.
def helper():
    return Expect(decoder(A)).on(404, decoder(B))
