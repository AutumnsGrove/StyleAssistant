"""Product extraction module."""

from backend.extractors.base import ProductExtractor
from backend.extractors.uniqlo import UniqloExtractor
from backend.extractors.factory import get_extractor, get_supported_sites, is_supported

__all__ = [
    "ProductExtractor",
    "UniqloExtractor",
    "get_extractor",
    "get_supported_sites",
    "is_supported",
]
