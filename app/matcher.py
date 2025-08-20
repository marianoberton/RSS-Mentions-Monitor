import re
from unidecode import unidecode
from typing import List, Optional, Tuple

def normalize_text(text: str) -> str:
    """Normalizes text by applying unidecode and casefolding."""
    return unidecode(text).casefold()

def find_keyword(text: str, keywords: List[str]) -> Optional[str]:
    """Finds the first matching keyword in the text."""
    normalized_text = normalize_text(text)
    for keyword in keywords:
        normalized_keyword = normalize_text(keyword)
        if re.search(r'\b' + re.escape(normalized_keyword) + r'\b', normalized_text):
            return keyword
    return None