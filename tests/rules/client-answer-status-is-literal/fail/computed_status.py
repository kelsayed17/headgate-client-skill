# A computed status is not a literal.
from http import HTTPStatus

FILING_OR_NONE = Expect(decoder(Filing)).on(404 + 0, nothing)
