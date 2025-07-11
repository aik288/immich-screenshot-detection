#!/usr/bin/env python3
"""
Immich Screenshot Categorizer
A dockerized application that identifies screenshots in an Immich photo library
"""

import asyncio
import logging
from typing import List, Dict, Any
from src.immich_client import ImmichClient
from src.screenshot_detector import ScreenshotDetector
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

    async def process_photos(self):
        """Main processing loop to categorize screenshots"""
        logger.info("Starting photo processing...")

        # Get all photos from Immich
        photos = await self.immich_client.get_all_photos()
        logger.info(f"Found {len(photos)} photos to process")

        screenshots_found = 0
        for i, photo in enumerate(photos, 1):
            try:
                logger.info(
                    f"Processing photo {i}/{len(photos)}: {photo.get('originalFileName', 'Unknown')}"
                )

                # Download photo data
                photo_data = await self.immich_client.download_photo(photo["id"])

                # Check if it's a screenshot
                is_screenshot = await self.screenshot_detector.is_screenshot(photo_data)

                if is_screenshot:
                    screenshots_found += 1
                    logger.info(
                        f"Screenshot detected: {photo.get('originalFileName', 'Unknown')}"
                    )

                    # Tag the photo as screenshot in Immich
                    await self.immich_client.tag_photo_as_screenshot(photo["id"])

            except Exception as e:
                logger.error(
                    f"Error processing photo {photo.get('id', 'Unknown')}: {str(e)}"
                )
                continue

        logger.info(
            f"Processing complete. Found {screenshots_found} screenshots out of {len(photos)} photos"
        )

    async def run(self):
        """Run the main application"""
        try:
            await self.initialize()
            await self.process_photos()
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            raise


async def main():
    """Main entry point"""
    try:
        # Load configuration
        config = Config()

        # Create and run the categorizer
        categorizer = ImmichScreenshotCategorizer(config)
        await categorizer.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
