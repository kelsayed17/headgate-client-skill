# The one honest exception: the answer is a CSRF token read from the cookie jar after a handshake, not a body, so it
# takes the reasoned allow comment (a Senate eFD client's accept_prohibition_agreement).
class C(AsyncBaseClient):
    async def accept_prohibition_agreement(self) -> str:  # headgate-verify: allow client-method-returns -- the answer is the csrftoken cookie the gate GET sets, not a body
        await self.get("search/home/", expect=nothing)
        return self._http_client.cookies.get("csrftoken", "")
