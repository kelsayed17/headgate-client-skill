FILING_OR_NONE = Expect(decoder(Filing)).on(HTTPStatus(404), nothing)
