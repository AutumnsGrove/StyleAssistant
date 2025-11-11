from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class ProductExtractor(ABC):
    """Base class for site-specific product extractors."""

    @abstractmethod
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract product data from HTML.

        Args:
            html: Page HTML content
            url: Product URL

        Returns:
            {
                "title": str,
                "price": float,
                "currency": str,
                "description": str,
                "materials": str,
                "category": str,
                "colors": List[str],
                "sizes": List[str],
                "images": List[str],  # URLs
                "url": str,
                "site": str  # e.g. 'uniqlo'
            }
        """
        pass

    @abstractmethod
    def detect(self, url: str) -> bool:
        """
        Check if this extractor can handle the URL.

        Args:
            url: Product URL

        Returns:
            True if this extractor supports the URL
        """
        pass

    def _clean_text(self, text: Optional[str]) -> str:
        """Remove extra whitespace and newlines."""
        if not text:
            return ""
        return " ".join(text.split())

    def _parse_price(self, price_str: str) -> tuple[float, str]:
        """
        Extract price and currency from string.

        Args:
            price_str: e.g. "$29.90" or "¥2,990"

        Returns:
            (price_float, currency_code)
        """
        import re

        # Remove commas
        price_str = price_str.replace(",", "")
        # Extract number
        match = re.search(r"[\d.]+", price_str)
        if not match:
            return 0.0, "USD"
        price = float(match.group())
        # Detect currency
        if "$" in price_str:
            currency = "USD"
        elif "¥" in price_str or "JPY" in price_str:
            currency = "JPY"
        elif "€" in price_str:
            currency = "EUR"
        else:
            currency = "USD"
        return price, currency
