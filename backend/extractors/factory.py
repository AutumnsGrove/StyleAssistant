"""
Extractor factory for selecting the appropriate product extractor.

Uses URL pattern matching to select the right extractor for each site.
"""

from typing import Optional
from backend.extractors.base import ProductExtractor
from backend.extractors.uniqlo import UniqloExtractor


# Registry of available extractors
_EXTRACTORS: list[ProductExtractor] = [
    UniqloExtractor(),
]


def get_extractor(url: str) -> Optional[ProductExtractor]:
    """
    Get the appropriate extractor for a URL.

    Uses each extractor's detect() method to find a match.

    Args:
        url: Product page URL

    Returns:
        ProductExtractor if supported site, None otherwise
    """
    for extractor in _EXTRACTORS:
        if extractor.detect(url):
            return extractor
    return None


def get_supported_sites() -> list[str]:
    """
    Get list of supported e-commerce sites.

    Returns:
        List of site names
    """
    return [ext.site_name for ext in _EXTRACTORS]


def is_supported(url: str) -> bool:
    """
    Check if a URL is from a supported site.

    Args:
        url: URL to check

    Returns:
        True if URL is from a supported site
    """
    return get_extractor(url) is not None
