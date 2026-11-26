#!/usr/bin/env python3
"""Minimal example of using the Immich client directly."""

import asyncio

from src.config import Config
from src.immich_client import ImmichClient


async def main():
    config = Config()

    async with ImmichClient(config) as client:
        photos = await client.get_all_photos()
        print(f"Found {len(photos)} image assets")

        for photo in photos[:5]:
            print(f"  {photo.get('originalFileName', 'Unknown')} ({photo['id']})")

        if photos:
            data = await client.download_photo(photos[0]["id"])
            print(f"Downloaded {len(data)} bytes for the first asset")


if __name__ == "__main__":
    asyncio.run(main())
