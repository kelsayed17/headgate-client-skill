FILING_OR_NONE = Expect(decoder(Filing)).on(HTTPStatus.NOT_FOUND.value, nothing)
