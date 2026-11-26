"""
Configuration management for the Immich Screenshot Categorizer
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """Application configuration management."""

    def __init__(self):
        base_url = self._get_env_var("IMMICH_SERVER_URL", "http://localhost:2283")
        # Immich exposes its REST API under /api; avoid doubling it if the user
        # already included the suffix.
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api"):
            base_url += "/api"
        self.immich_server_url = base_url

        self.immich_api_key = self._get_env_var("IMMICH_API_KEY")
        # Optional: the API key already identifies the user. Kept for backwards
        # compatibility with existing .env files.
        self.immich_user_id = self._get_env_var("IMMICH_USER_ID", "")

        # Screenshot detection settings
        self.screenshot_confidence_threshold = self._get_float_env_var(
            "SCREENSHOT_CONFIDENCE_THRESHOLD", "0.7"
        )
        self.batch_size = self._get_int_env_var("BATCH_SIZE", "10")
        self.max_image_size = self._get_int_env_var("MAX_IMAGE_SIZE", "2048")

        # Logging settings
        self.log_level = self._get_env_var("LOG_LEVEL", "INFO").upper()

        # Tag settings
        self.screenshot_tag = self._get_env_var("SCREENSHOT_TAG", "screenshot")
        self.create_album = self._get_env_var("CREATE_ALBUM", "true").lower() == "true"
        self.album_name = self._get_env_var("ALBUM_NAME", "Screenshots")

        # Validate required configuration
        self._validate_config()

    def _get_env_var(self, key: str, default: Optional[str] = None) -> str:
        """Get an environment variable with an optional default."""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is required")
        return value

    def _get_int_env_var(self, key: str, default: str) -> int:
        """Get a positive integer environment variable."""
        raw = self._get_env_var(key, default)
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{key} must be an integer, got {raw!r}") from exc
        if value <= 0:
            raise ValueError(f"{key} must be greater than zero, got {value}")
        return value

    def _get_float_env_var(self, key: str, default: str) -> float:
        """Get a float environment variable."""
        raw = self._get_env_var(key, default)
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"{key} must be a number, got {raw!r}") from exc

    def _validate_config(self):
        """Validate required configuration values."""
        if not self.immich_api_key:
            raise ValueError("Missing required environment variable: IMMICH_API_KEY")

        if not self.immich_server_url.startswith(("http://", "https://")):
            raise ValueError("IMMICH_SERVER_URL must start with http:// or https://")

        if not 0.0 <= self.screenshot_confidence_threshold <= 1.0:
            raise ValueError(
                "SCREENSHOT_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0"
            )

        logger.info("Configuration loaded successfully:")
        logger.info("  Server URL: %s", self.immich_server_url)
        logger.info(
            "  Screenshot confidence threshold: %s",
            self.screenshot_confidence_threshold,
        )
        logger.info("  Batch size: %s", self.batch_size)
        logger.info("  Max image size: %s", self.max_image_size)
        logger.info("  Screenshot tag: %s", self.screenshot_tag)
        logger.info("  Create album: %s", self.create_album)
        if self.create_album:
            logger.info("  Album name: %s", self.album_name)
