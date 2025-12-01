"""
Image optimization utility for GroveAssistant.

Handles:
- Downloading product images from URLs
- Converting to WebP format
- Compressing to target size
- Returning optimized image bytes
"""

import io
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from PIL import Image

logger = logging.getLogger("grove_assistant.image_optimizer")

# Configuration
DEFAULT_MAX_SIZE_KB = 200  # Max file size in KB
DEFAULT_MAX_DIMENSION = 1200  # Max width or height in pixels
DEFAULT_QUALITY = 85  # Initial quality setting
MIN_QUALITY = 30  # Minimum quality to try
QUALITY_STEP = 10  # Quality reduction per iteration
SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
REQUEST_TIMEOUT = 30  # Seconds


class ImageOptimizer:
    """
    Image optimizer for product images.

    Converts images to WebP format and compresses to target size.
    """

    def __init__(
        self,
        max_size_kb: int = DEFAULT_MAX_SIZE_KB,
        max_dimension: int = DEFAULT_MAX_DIMENSION,
        initial_quality: int = DEFAULT_QUALITY,
    ):
        """
        Initialize the optimizer.

        Args:
            max_size_kb: Maximum file size in KB
            max_dimension: Maximum width or height in pixels
            initial_quality: Starting quality for WebP compression
        """
        self.max_size_bytes = max_size_kb * 1024
        self.max_dimension = max_dimension
        self.initial_quality = initial_quality

    async def optimize_from_url(
        self, url: str
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Download and optimize an image from URL.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (optimized_bytes, error_message)
            If successful, error_message is None
            If failed, optimized_bytes is None
        """
        try:
            # Download image
            image_data = await self._download_image(url)
            if not image_data:
                return None, "Failed to download image"

            # Optimize
            return self.optimize_bytes(image_data), None

        except Exception as e:
            logger.error(f"Failed to optimize image from {url}: {e}")
            return None, str(e)

    def optimize_bytes(self, image_data: bytes) -> bytes:
        """
        Optimize image bytes to WebP format.

        Args:
            image_data: Raw image bytes

        Returns:
            Optimized WebP image bytes
        """
        # Open image
        img = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (WebP doesn't support all modes)
        if img.mode in ("RGBA", "P"):
            # Preserve transparency for RGBA
            if img.mode == "RGBA":
                pass  # WebP supports RGBA
            else:
                img = img.convert("RGBA")
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if too large
        img = self._resize_if_needed(img)

        # Compress to target size
        return self._compress_to_target(img)

    def _resize_if_needed(self, img: Image.Image) -> Image.Image:
        """Resize image if it exceeds max dimensions."""
        width, height = img.size

        if width <= self.max_dimension and height <= self.max_dimension:
            return img

        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))

        logger.debug(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _compress_to_target(self, img: Image.Image) -> bytes:
        """Compress image to target size using iterative quality reduction."""
        quality = self.initial_quality

        while quality >= MIN_QUALITY:
            buffer = io.BytesIO()
            img.save(buffer, format="WEBP", quality=quality, method=4)
            data = buffer.getvalue()

            if len(data) <= self.max_size_bytes:
                logger.debug(
                    f"Compressed to {len(data) / 1024:.1f}KB at quality {quality}"
                )
                return data

            quality -= QUALITY_STEP

        # Return lowest quality version if still over target
        buffer = io.BytesIO()
        img.save(buffer, format="WEBP", quality=MIN_QUALITY, method=6)
        data = buffer.getvalue()
        logger.warning(
            f"Could not reach target size. Final size: {len(data) / 1024:.1f}KB"
        )
        return data

    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            # Validate URL
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                logger.error(f"Invalid URL scheme: {parsed.scheme}")
                return None

            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; GroveAssistant/1.0)"
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"Failed to download image: HTTP {response.status_code}"
                    )
                    return None

                # Check content type
                content_type = response.headers.get("content-type", "").split(";")[0]
                if content_type not in SUPPORTED_FORMATS:
                    logger.warning(f"Unsupported image format: {content_type}")
                    # Try anyway - PIL might handle it

                return response.content

        except httpx.TimeoutException:
            logger.error(f"Timeout downloading image from {url}")
            return None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None


# Convenience function
async def optimize_image_url(
    url: str,
    max_size_kb: int = DEFAULT_MAX_SIZE_KB,
    max_dimension: int = DEFAULT_MAX_DIMENSION,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Convenience function to optimize an image from URL.

    Args:
        url: Image URL
        max_size_kb: Maximum file size in KB
        max_dimension: Maximum width/height

    Returns:
        Tuple of (optimized_bytes, error_message)
    """
    optimizer = ImageOptimizer(max_size_kb=max_size_kb, max_dimension=max_dimension)
    return await optimizer.optimize_from_url(url)
