import pytest
from app.matcher import normalize_text, find_keyword

def test_normalize_text():
    assert normalize_text("Axel Kicillof") == "axel kicillof"
    assert normalize_text("Javier Milei") == "javier milei"
    assert normalize_text("Cristina Fernández de Kirchner") == "cristina fernandez de kirchner"

def test_find_keyword():
    keywords = ["Axel Kicillof", "Javier Milei"]
    text = "El gobernador Axel Kicillof anunció nuevas medidas."
    assert find_keyword(text, keywords) == "Axel Kicillof"

    text = "Javier Milei viaja a Estados Unidos."
    assert find_keyword(text, keywords) == "Javier Milei"

    text = "El presidente se reunió con su gabinete."
    assert find_keyword(text, keywords) is None