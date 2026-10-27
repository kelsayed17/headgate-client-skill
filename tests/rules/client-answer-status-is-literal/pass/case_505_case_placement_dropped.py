# Placement no longer matters (answers are declared at module level); the status is a literal, so this passes.
async def helper(client):
    def inner():
        return Expect(decoder(A), answers={404: decoder(B)})
    return inner
