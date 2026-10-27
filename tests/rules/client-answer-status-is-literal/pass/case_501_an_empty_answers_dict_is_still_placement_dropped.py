# Placement no longer matters (answers are declared at module level); the status is a literal, so this passes.
# An empty answers dict is still a claim, and outside a method it is misplaced.
_EMPTY = Expect(decoder(A), {})
