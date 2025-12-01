"""
Pydantic models for product-related API requests and responses.

Defines the structure of product data with validation.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base product fields shared across models."""

    title: str = Field(..., description="Product name/title")
    price: float = Field(..., ge=0, description="Product price")
    currency: str = Field(default="USD", description="Price currency code")
    description: Optional[str] = Field(None, description="Product description")
    materials: Optional[str] = Field(None, description="Material composition")
    category: Optional[str] = Field(None, description="Product category")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    sizes: List[str] = Field(default_factory=list, description="Available sizes")


class ProductCreate(ProductBase):
    """Product creation request model."""

    product_url: str = Field(..., description="Product page URL")
    site: str = Field(..., description="E-commerce site identifier")
    images: List[str] = Field(default_factory=list, description="Product image URLs")


class ProductResponse(ProductBase):
    """Product response model with database fields."""

    id: int = Field(..., description="Database ID")
    product_url: str = Field(..., description="Product page URL")
    site: str = Field(..., description="E-commerce site identifier")
    first_seen: datetime = Field(..., description="First time product was seen")
    last_seen: datetime = Field(..., description="Last time product was seen")

    class Config:
        from_attributes = True


class ProductExtracted(BaseModel):
    """Product data as extracted from a page (before database storage)."""

    title: str
    price: float
    currency: str = "USD"
    description: str = ""
    materials: str = ""
    category: str = ""
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    url: str
    site: str
