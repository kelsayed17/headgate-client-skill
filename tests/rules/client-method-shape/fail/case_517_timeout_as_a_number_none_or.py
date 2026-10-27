# timeout= as a number, None or a Timeouts built at the call: headgate 0.6.0 takes only a Timeouts, and one built per
# call is a module constant.
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=as_bytes, timeout=60)
