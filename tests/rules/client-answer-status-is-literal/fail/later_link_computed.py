# Every link of a chain is read, not only the first.
FILING_OR_NONE = Expect(decoder(Filing)).on(HTTPStatus.NOT_FOUND, nothing).on(400 + 10, decoder(Gone))
