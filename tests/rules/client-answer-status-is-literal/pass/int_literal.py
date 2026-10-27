# An int literal, at module level, chained, by keyword, and in the answers table.
FILING_OR_NONE = Expect(decoder(Filing)).on(404, nothing).on(status=410, read=nothing)
TABLE = Expect(decoder(Filing), {404: nothing, (409): decoder(Conflict)})
