# `.on` on a module-level reader name extends that reader: its status is read too.
FILING_OR_NONE = Expect(decoder(Filing)).on(404, nothing)
FILING_OR_GONE = FILING_OR_NONE.on(gone_status(), nothing)
