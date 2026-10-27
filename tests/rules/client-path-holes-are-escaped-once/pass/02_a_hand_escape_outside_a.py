from urllib.parse import quote


def house_ptr_pdf_url(year: int, doc_id: str) -> str:
    return f"{_HOUSE_BASE_URL}public_disc/ptr-pdfs/{year}/{quote(doc_id, safe='')}.pdf"


url = _BASE + "/" + quote(symbol, safe="")
joined = "/".join(seg(p) for p in parts)
