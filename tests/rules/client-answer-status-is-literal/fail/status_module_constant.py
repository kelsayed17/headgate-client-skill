# A name, even an UPPER_CASE constant, is not a literal: write the literal or the HTTPStatus member.
NOT_FOUND = 404
FILING_OR_NONE = Expect(decoder(Filing)).on(NOT_FOUND, nothing)
