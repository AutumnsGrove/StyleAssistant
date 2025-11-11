from backend.extractors.base import ProductExtractor
from backend.extractors.uniqlo import UniqloExtractor
from typing import Optional

# Registry of available extractors
EXTRACTORS = [
    UniqloExtractor(),
]


def get_extractor(url: str) -> Optional[ProductExtractor]:
    """
    Get appropriate extractor for URL.

    Args:
        url: Product page URL

    Returns:
        Extractor instance or None if unsupported
    """
    for extractor in EXTRACTORS:
        if extractor.detect(url):
            return extractor
    return None
