#!/usr/bin/env python3
"""
Immich Screenshot Categorizer
A dockerized application that identifies screenshots in an Immich photo library
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from src.config import Config
from src.immich_client import ImmichClient
from src.screenshot_detector import ScreenshotDetector

# Configure logging early so configuration messages respect LOG_LEVEL.
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ImmichScreenshotCategorizer:
    def __init__(self, config: Config):
        self.config = config
        self.immich_client = ImmichClient(config)
        self.screenshot_detector = ScreenshotDetector(config)

    async def initialize(self):
        """Initialize the application components"""
        logger.info("Initializing Immich Screenshot Categorizer...")
        await self.immich_client.initialize()
        logger.info("Initialization complete")

    async def _process_photo(self, photo: Dict[str, Any]) -> Optional[str]:
        """Return the asset id if the photo is a screenshot, else None."""
        asset_id = photo["id"]
        name = photo.get("originalFileName", "Unknown")

        photo_data = await self.immich_client.download_photo(asset_id)
        if not photo_data:
            logger.warning("Skipping %s: could not download asset", name)
            return None

        if not await self.screenshot_detector.is_screenshot(photo_data):
            return None

        logger.info("Screenshot detected: %s", name)

        # Tagging is best-effort; the asset still belongs in the album.
        await self.immich_client.tag_photo_as_screenshot(asset_id)
        return asset_id

    async def process_photos(self) -> List[str]:
        """Main processing loop to categorize screenshots"""
        logger.info("Starting photo processing...")

        photos = await self.immich_client.get_all_photos()
        logger.info("Found %s photos to process", len(photos))

        screenshot_ids: List[str] = []
        batch_size = self.config.batch_size

        for start in range(0, len(photos), batch_size):
            batch = photos[start : start + batch_size]
            results = await asyncio.gather(
                *(self._process_photo(photo) for photo in batch),
                return_exceptions=True,
            )

            for offset, (photo, result) in enumerate(zip(batch, results), start=1):
                label = f"{start + offset}/{len(photos)}"
                if isinstance(result, Exception):
                    logger.error(
                        "Error processing photo %s (%s): %s",
                        photo.get("id", "Unknown"),
                        label,
                        result,
                    )
                elif result:
                    screenshot_ids.append(result)

            logger.info(
                "Processed batch %s-%s of %s",
                start + 1,
                start + len(batch),
                len(photos),
            )

        logger.info(
            "Processing complete. Found %s screenshots out of %s photos",
            len(screenshot_ids),
            len(photos),
        )

        if screenshot_ids and self.config.create_album:
            await self.immich_client.create_screenshot_album(screenshot_ids)

        return screenshot_ids

    async def run(self):
        """Run the main application"""
        await self.initialize()
        try:
            await self.process_photos()
        finally:
            await self.immich_client.close()


async def main() -> int:
    """Main entry point"""
    try:
        config = Config()
        categorizer = ImmichScreenshotCategorizer(config)
        await categorizer.run()
        return 0
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        logger.debug("Traceback:", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
