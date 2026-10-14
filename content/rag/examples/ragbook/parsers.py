from html.parser import HTMLParser
from pathlib import Path


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if not self.skip and tag in ("p", "div", "h1", "h2", "h3", "li", "tr", "br"):
            self.output.append("\n")
        if not self.skip and tag in ("td", "th"):
            self.output.append("\t")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        if not self.skip and tag in ("p", "div", "h1", "h2", "h3", "li", "tr"):
            self.output.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.output.append(data)


def html_text(html):
    if len(html) > 1_000_000:
        raise ValueError("HTML too large")
    parser = TextHTML()
    parser.feed(html)
    return "".join(parser.output).strip()


def pdf_pages(path, max_pages=50, max_bytes=10 * 1024 * 1024):
    from pypdf import PdfReader

    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError("PDF too large")
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError("encrypted PDF is not supported")
    if len(reader.pages) > max_pages:
        raise ValueError("too many pages")
    result = []
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        result.append({"page": number, "text": text, "needs_ocr": not text.strip()})
    return result


# 텍스트 레이어 추출만 구현했다. OCR·표 셀 재구성·레이아웃 좌표 복원은 별도 단계다.
