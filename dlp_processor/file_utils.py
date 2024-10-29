import io

from pdfminer.high_level import extract_text


def extract_text_from_pdf(content):
    with io.BytesIO(content) as f:
        text = extract_text(f)
    return text
