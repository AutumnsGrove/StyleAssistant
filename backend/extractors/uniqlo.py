from backend.extractors.base import ProductExtractor
from typing import Dict, Any
from bs4 import BeautifulSoup


class UniqloExtractor(ProductExtractor):
    """Extractor for Uniqlo product pages."""

    def __init__(self):
        self.site_name = "uniqlo"
        self.url_patterns = ["uniqlo.com", "uniqlo.jp"]

    def detect(self, url: str) -> bool:
        """Check if URL is a Uniqlo product page."""
        return any(pattern in url.lower() for pattern in self.url_patterns)

    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """Extract product data from Uniqlo page."""
        soup = BeautifulSoup(html, "html.parser")

        # Note: These selectors are placeholders
        # In reality, you'd need to inspect actual Uniqlo pages
        # For MVP, we'll use generic selectors that might work

        # Extract title
        title_elem = soup.find("h1", class_="product-title") or soup.find("h1")
        title = self._clean_text(title_elem.text if title_elem else "")

        # Extract price
        price_elem = soup.find(class_="price") or soup.find(
            "span", class_="product-price"
        )
        price_str = price_elem.text if price_elem else "$0.00"
        price, currency = self._parse_price(price_str)

        # Extract description
        desc_elem = soup.find(class_="product-description") or soup.find(
            "div", class_="description"
        )
        description = self._clean_text(desc_elem.text if desc_elem else "")

        # Extract materials
        materials_elem = soup.find(class_="materials") or soup.find(
            string=lambda t: t and "Material" in t
        )
        materials = self._clean_text(materials_elem.text if materials_elem else "")

        # Extract category
        category_elem = soup.find(class_="category") or soup.find("nav")
        category = self._clean_text(category_elem.text if category_elem else "clothing")

        # Extract colors (simplified)
        colors = []
        color_elems = soup.find_all(class_="color-option") or soup.find_all(
            "button", attrs={"data-color": True}
        )
        for elem in color_elems[:10]:  # Limit to 10 colors
            color = elem.get("data-color") or elem.get("aria-label", "")
            if color:
                colors.append(self._clean_text(color))

        # Extract sizes (simplified)
        sizes = []
        size_elems = soup.find_all(class_="size-option") or soup.find_all(
            "button", attrs={"data-size": True}
        )
        for elem in size_elems[:20]:  # Limit to 20 sizes
            size = elem.get("data-size") or elem.text
            if size:
                sizes.append(self._clean_text(size))

        # Extract images
        images = []
        img_elems = (
            soup.find_all("img", class_="product-image") or soup.find_all("img")[:10]
        )
        for elem in img_elems:
            src = elem.get("src") or elem.get("data-src")
            if src and "product" in src.lower():
                images.append(src)

        return {
            "title": title,
            "price": price,
            "currency": currency,
            "description": description,
            "materials": materials,
            "category": category,
            "colors": colors or ["default"],
            "sizes": sizes or ["one-size"],
            "images": images,
            "url": url,
            "site": self.site_name,
        }
