"""Product management module."""

from backend.products.service import ProductService
from backend.products.models import ProductCreate, ProductResponse, ProductExtracted

__all__ = ["ProductService", "ProductCreate", "ProductResponse", "ProductExtracted"]
