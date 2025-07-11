"""
Immich API Client for accessing photos and metadata using immich-python-sdk
"""

import logging
from typing import List, Dict, Any, Optional
from immich_python_sdk import ApiClient, Configuration
from immich_python_sdk.api.assets_api import AssetsApi
from immich_python_sdk.api.albums_api import AlbumsApi
from immich_python_sdk.api.server_api import ServerApi
from immich_python_sdk.api.search_api import SearchApi
from immich_python_sdk.models.create_album_dto import CreateAlbumDto
from immich_python_sdk.models.bulk_ids_dto import BulkIdsDto
from immich_python_sdk.models.update_asset_dto import UpdateAssetDto
from immich_python_sdk.models.metadata_search_dto import MetadataSearchDto
from immich_python_sdk.models.asset_type_enum import AssetTypeEnum

logger = logging.getLogger(__name__)


class ImmichClient:
    """Client for interacting with the Immich API using immich-python-sdk"""

    def __init__(self, config):
        self.config = config

        # Configure API client
        configuration = Configuration(
            host=config.immich_server_url,  # Don't strip trailing slash as it's needed
            api_key={"api_key": config.immich_api_key},
        )
        self.api_client = ApiClient(configuration)

        # Initialize API interfaces
        self.assets_api = AssetsApi(self.api_client)
        self.albums_api = AlbumsApi(self.api_client)
        self.server_api = ServerApi(self.api_client)
        self.search_api = SearchApi(self.api_client)

    async def initialize(self):
        """Initialize the API client"""
        try:
            # Test connection
            self._test_connection()
            logger.info("Successfully initialized Immich client")
        except Exception as e:
            logger.error(f"Failed to initialize Immich client: {str(e)}")
            raise

    def _test_connection(self):
        """Test the connection to Immich server"""
        try:
            response = self.server_api.ping_server()
            if not response:
                raise ConnectionError("Immich server ping failed")
        except Exception as e:
            logger.error(f"Failed to connect to Immich server: {str(e)}")
            raise

    async def get_all_photos(self) -> List[Dict[str, Any]]:
        """Get all photos from Immich"""
        photos = []
        page = 1
        page_size = 1000

        while True:
            try:
                # Create search parameters
                search_params = MetadataSearchDto.model_validate(
                    {"page": page, "size": page_size, "type": AssetTypeEnum("IMAGE")}
                )

                # Search for assets
                response = self.search_api.search_assets(search_params)

                if not response.assets.items:
                    break

                # Convert to dict
                image_photos = [asset.to_dict() for asset in response.assets.items]

                photos.extend(image_photos)
                logger.info(f"Retrieved {len(image_photos)} photos from page {page}")

                # Check if we've reached the end
                if len(response.assets.items) < page_size:
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error retrieving photos on page {page}: {str(e)}")
                break

        logger.info(f"Retrieved total of {len(photos)} photos")
        return photos

    async def download_photo(self, asset_id: str) -> bytes:
        """Download photo data by asset ID"""
        try:
            response = self.assets_api.download_asset(id=asset_id)
            return response
        except Exception as e:
            logger.error(f"Error downloading photo {asset_id}: {str(e)}")
            return b""

    async def tag_photo_as_screenshot(self, asset_id: str) -> bool:
        """Tag a photo as a screenshot"""
        try:
            # Get asset details
            asset = self.assets_api.get_asset_info(id=asset_id)
            existing_tags = getattr(asset, "tags", []) or []

            # Add screenshot tag if not already present
            if self.config.screenshot_tag not in existing_tags:
                new_tags = existing_tags + [self.config.screenshot_tag]

                # Update asset with new tags
                update_dto = UpdateAssetDto.model_validate({"tags": new_tags})
                self.assets_api.update_asset(id=asset_id, update_asset_dto=update_dto)

                logger.info(f"Successfully tagged photo {asset_id} as screenshot")
                return True
            else:
                logger.info(f"Photo {asset_id} already tagged as screenshot")
                return True

        except Exception as e:
            logger.error(f"Error tagging photo {asset_id}: {str(e)}")
            return False

    async def create_screenshot_album(self, asset_ids: List[str]) -> bool:
        """Create an album for screenshots"""
        if not self.config.create_album:
            return True

        try:
            # Get all albums
            albums = self.albums_api.get_all_albums()

            # Find existing album
            existing_album = next(
                (
                    album
                    for album in albums
                    if album.album_name == self.config.album_name
                ),
                None,
            )

            if existing_album:
                # Add assets to existing album
                bulk_ids = BulkIdsDto.model_validate({"ids": asset_ids})
                self.albums_api.add_assets_to_album(
                    id=existing_album.id, bulk_ids_dto=bulk_ids
                )
                logger.info(
                    f"Added {len(asset_ids)} assets to existing album '{self.config.album_name}'"
                )
                return True
            else:
                # Create new album
                create_dto = CreateAlbumDto.model_validate(
                    {
                        "albumName": self.config.album_name,
                        "description": "Screenshots detected automatically",
                        "assetIds": asset_ids,
                    }
                )
                self.albums_api.create_album(create_album_dto=create_dto)
                logger.info(
                    f"Created new album '{self.config.album_name}' with {len(asset_ids)} assets"
                )
                return True

        except Exception as e:
            logger.error(f"Error creating screenshot album: {str(e)}")
            return False

        return False
