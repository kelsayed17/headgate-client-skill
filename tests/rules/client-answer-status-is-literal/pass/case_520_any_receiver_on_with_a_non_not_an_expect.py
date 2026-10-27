# Only an `.on` on an Expect chain (or an UPPER_CASE reader name) is a claim: an event bus's `.on` is not.
# Any receiver: `.on` with a non-literal first argument is read as a claim, as the test read it.
class C:
    def n(self, bus):
        bus.on("tick", self.handle)
