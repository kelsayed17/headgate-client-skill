# timeout= or deadline= computed at the call, or a constant in disguise: a call, arithmetic, a subscript, a
# conditional, a negation, a dotted or lowercase or CamelCase name. And a constant for the other knobs.
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=as_bytes, timeout=60, deadline=full_attempts_deadline(60))
