from app.ingestion.parsers import extract_raw_ideas_from_upload


def test_csv_upload_parser():
    content = b"raw_text\nGi\xe1\xba\xa3m \xc4\x91\xe1\xbb\x99 d\xc3\xa0y lon 330ml\n"
    parsed = extract_raw_ideas_from_upload("ideas.csv", content)
    assert parsed.parser == "csv"
    assert len(parsed.raw_ideas) == 1


def test_image_upload_requires_ocr():
    parsed = extract_raw_ideas_from_upload("whiteboard.png", b"fake")
    assert parsed.parser == "ocr_required"
    assert not parsed.raw_ideas
    assert parsed.warnings
