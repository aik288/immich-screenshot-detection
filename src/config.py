"""
Configuration management for the Immich Screenshot Categorizer
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Application configuration management"""

    def __init__(self):
        base_url = self._get_env_var("IMMICH_SERVER_URL", "http://localhost:2283")
        # Ensure the URL ends with /api
        self.immich_server_url = base_url.rstrip("/") + "/api"

        self.immich_api_key = self._get_env_var("IMMICH_API_KEY")
        self.immich_user_id = self._get_env_var("IMMICH_USER_ID")

        # Screenshot detection settings
        self.screenshot_confidence_threshold = float(
            self._get_env_var("SCREENSHOT_CONFIDENCE_THRESHOLD", "0.7")
        )
        self.batch_size = int(self._get_env_var("BATCH_SIZE", "10"))
        self.max_image_size = int(self._get_env_var("MAX_IMAGE_SIZE", "2048"))

        # Logging settings
        self.log_level = self._get_env_var("LOG_LEVEL", "INFO")

        # Tag settings
        self.screenshot_tag = self._get_env_var("SCREENSHOT_TAG", "screenshot")
        self.create_album = self._get_env_var("CREATE_ALBUM", "false").lower() == "true"
        self.album_name = self._get_env_var("ALBUM_NAME", "Screenshots")

        # Validate required configuration
        self._validate_config()

    def _get_env_var(self, key: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is required")
        return value

    def _validate_config(self):
        """Validate required configuration values"""
        required_vars = ["immich_api_key"]
        missing_vars = []

        for var in required_vars:
            if not getattr(self, var):
                missing_vars.append(var.upper())

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Validate URL format
        if not self.immich_server_url.startswith(("http://", "https://")):
            raise ValueError("IMMICH_SERVER_URL must start with http:// or https://")

        logger.info(f"Configuration loaded successfully:")
        logger.info(f"  Server URL: {self.immich_server_url}")
        logger.info(
            f"  Screenshot confidence threshold: {self.screenshot_confidence_threshold}"
        )
        logger.info(f"  Batch size: {self.batch_size}")
        logger.info(f"  Max image size: {self.max_image_size}")
        logger.info(f"  Screenshot tag: {self.screenshot_tag}")
        logger.info(f"  Create album: {self.create_album}")
        if self.create_album:
            logger.info(f"  Album name: {self.album_name}")
