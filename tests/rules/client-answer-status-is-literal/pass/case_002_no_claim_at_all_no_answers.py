# No claim at all: no answers, `.on` with no status, an `ok=` alone. Anywhere, even at module level. (An EMPTY dict
# is a claim of nothing: fine in a method, misplaced outside one, as the test's `_claimed` returned [] for it.)
_SPEC = Expect(decoder(A))
_KW = Expect(ok=decoder(A))
_NONE = thing.on()
_SPLAT = thing.on(**options)
spec: Expect[T] = expect if isinstance(expect, Expect) else Expect(expect)
