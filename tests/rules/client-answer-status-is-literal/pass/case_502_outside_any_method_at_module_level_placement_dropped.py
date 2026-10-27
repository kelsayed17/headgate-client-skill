# Placement no longer matters (answers are declared at module level); the status is a literal, so this passes.
# Outside any method: at module level, in a module-level function, nested in one, in a class body, in a lambda at
# class level, and in a def under an `if` in a class body (not a method: its parent is the if).
_TOP = Expect(decoder(A)).on(404, nothing)
