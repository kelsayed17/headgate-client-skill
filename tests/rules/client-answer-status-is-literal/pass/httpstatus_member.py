# An `HTTPStatus` member, bare or through the module, at module level and chained.
import http
from http import HTTPStatus

FILING = decoder(Filing)
FILING_OR_NONE = Expect(FILING).on(HTTPStatus.NOT_FOUND, nothing)
ORDER_OR_REJECTION = Expect(ORDER).on(http.HTTPStatus.UNPROCESSABLE_ENTITY, decoder(Rejection)).on(
    status=HTTPStatus.CONFLICT, read=decoder(Conflict)
)
EXTENDED = FILING_OR_NONE.on(HTTPStatus.GONE, nothing)
