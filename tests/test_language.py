from src.language import detect_language


def test_detect_english():
    assert detect_language("This is clearly an English sentence about work.") == "en"


def test_detect_german():
    assert detect_language("Dies ist ein deutscher Satz über die Arbeit.") == "de"


def test_empty_returns_fallback():
    assert detect_language("") == "en"
    assert detect_language("   ", fallback="de") == "de"


def test_undetectable_returns_fallback():
    # Digits/punctuation give langdetect nothing to work with.
    assert detect_language("12345 67890 !!!", fallback="en") == "en"
