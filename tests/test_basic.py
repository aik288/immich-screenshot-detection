"""
Basic tests for the Immich Screenshot Categorizer
"""

import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch

# Add the project root to the path so ``src`` is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestBasicImports(unittest.TestCase):
    """Test that all modules can be imported correctly"""

    def test_config_import(self):
        from src.config import Config

        self.assertTrue(hasattr(Config, "__init__"))

    def test_immich_client_import(self):
        from src.immich_client import ImmichClient

        self.assertTrue(hasattr(ImmichClient, "__init__"))

    def test_screenshot_detector_import(self):
        from src.screenshot_detector import ScreenshotDetector

        self.assertTrue(hasattr(ScreenshotDetector, "__init__"))


class TestConfigModule(unittest.TestCase):
    """Test the configuration module"""

    @patch.dict(
        os.environ,
        {"IMMICH_API_KEY": "test-key", "IMMICH_USER_ID": "test-user"},
        clear=True,
    )
    def test_config_creation(self):
        from src.config import Config

        config = Config()
        self.assertEqual(config.immich_api_key, "test-key")
        self.assertEqual(config.immich_user_id, "test-user")
        self.assertEqual(config.immich_server_url, "http://localhost:2283/api")
        self.assertTrue(config.create_album)

    @patch.dict(os.environ, {}, clear=True)
    def test_config_missing_required_vars(self):
        from src.config import Config

        with self.assertRaises(ValueError):
            Config()

    @patch.dict(
        os.environ,
        {
            "IMMICH_API_KEY": "test-key",
            "SCREENSHOT_CONFIDENCE_THRESHOLD": "1.5",
        },
        clear=True,
    )
    def test_config_rejects_invalid_threshold(self):
        from src.config import Config

        with self.assertRaises(ValueError):
            Config()

    @patch.dict(
        os.environ,
        {"IMMICH_API_KEY": "test-key", "IMMICH_SERVER_URL": "http://immich:2283/"},
        clear=True,
    )
    def test_config_normalizes_server_url(self):
        from src.config import Config

        config = Config()
        self.assertEqual(config.immich_server_url, "http://immich:2283/api")

    @patch.dict(
        os.environ,
        {"IMMICH_API_KEY": "test-key", "IMMICH_SERVER_URL": "http://immich:2283/api"},
        clear=True,
    )
    def test_config_does_not_double_api_suffix(self):
        from src.config import Config

        config = Config()
        self.assertEqual(config.immich_server_url, "http://immich:2283/api")


def make_config(**overrides):
    config = Mock()
    config.immich_server_url = "http://localhost:3001/api"
    config.immich_api_key = "test-key"
    config.immich_user_id = "test-user"
    config.screenshot_tag = "screenshot"
    config.create_album = True
    config.album_name = "Screenshots"
    config.screenshot_confidence_threshold = 0.7
    config.max_image_size = 2048
    config.batch_size = 10
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


class TestImmichClient(unittest.TestCase):
    """Test the Immich client"""

    def test_immich_client_creation(self):
        from src.immich_client import ImmichClient

        client = ImmichClient(make_config())
        self.assertEqual(client.base_url, "http://localhost:3001/api")
        self.assertEqual(client.api_key, "test-key")


class TestImmichClientAsync(unittest.IsolatedAsyncioTestCase):
    """Test the async Immich client against mocked API responses."""

    def setUp(self):
        from src.immich_client import ImmichClient

        self.client = ImmichClient(make_config())

    async def test_get_all_photos_paginates(self):
        self.client._request = AsyncMock(
            side_effect=[
                {"assets": {"items": [{"id": "a"}], "nextPage": "2"}},
                {"assets": {"items": [{"id": "b"}], "nextPage": None}},
            ]
        )

        photos = await self.client.get_all_photos()

        self.assertEqual([photo["id"] for photo in photos], ["a", "b"])
        self.assertEqual(self.client._request.await_count, 2)
        self.client._request.assert_any_await(
            "POST",
            "/search/metadata",
            json={"page": 1, "size": 1000, "type": "IMAGE"},
        )

    async def test_tag_photo_uses_tags_endpoint(self):
        self.client._tag_id = "tag-1"
        self.client._request = AsyncMock(
            return_value=[{"id": "asset-1", "success": True}]
        )

        tagged = await self.client.tag_photo_as_screenshot("asset-1")

        self.assertTrue(tagged)
        self.client._request.assert_awaited_once_with(
            "PUT", "/tags/tag-1/assets", json={"ids": ["asset-1"]}
        )

    async def test_create_album_creates_when_missing(self):
        self.client._request = AsyncMock(
            side_effect=[[], {"id": "album-1"}]
        )

        created = await self.client.create_screenshot_album(["a", "b"])

        self.assertTrue(created)
        self.client._request.assert_any_await(
            "POST",
            "/albums",
            json={
                "albumName": "Screenshots",
                "description": "Screenshots detected automatically",
                "assetIds": ["a", "b"],
            },
        )

    async def test_create_album_adds_to_existing(self):
        self.client._request = AsyncMock(
            side_effect=[
                [{"id": "album-1", "albumName": "Screenshots"}],
                [{"id": "a", "success": True}],
            ]
        )

        created = await self.client.create_screenshot_album(["a"])

        self.assertTrue(created)
        self.client._request.assert_any_await(
            "PUT", "/albums/album-1/assets", json={"ids": ["a"]}
        )

    async def test_create_album_noop_when_disabled(self):
        self.client.config.create_album = False
        self.client._request = AsyncMock()

        created = await self.client.create_screenshot_album(["a"])

        self.assertTrue(created)
        self.client._request.assert_not_awaited()


class TestScreenshotDetector(unittest.IsolatedAsyncioTestCase):
    """Test the screenshot detector"""

    def setUp(self):
        from src.screenshot_detector import ScreenshotDetector

        self.detector = ScreenshotDetector(make_config())

    def test_screenshot_detector_creation(self):
        self.assertEqual(self.detector.confidence_threshold, 0.7)
        self.assertEqual(self.detector.max_image_size, 2048)

    async def test_invalid_image_data_is_not_a_screenshot(self):
        self.assertFalse(await self.detector.is_screenshot(b"not an image"))
        self.assertFalse(await self.detector.is_screenshot(b""))


class TestMainApplication(unittest.TestCase):
    """Test the main application"""

    @patch("main.Config")
    @patch("main.ImmichClient")
    @patch("main.ScreenshotDetector")
    def test_main_application_creation(
        self, mock_detector, mock_client, mock_config
    ):
        from main import ImmichScreenshotCategorizer

        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance

        app = ImmichScreenshotCategorizer(mock_config_instance)

        self.assertIsNotNone(app)
        self.assertEqual(app.config, mock_config_instance)
        mock_client.assert_called_once_with(mock_config_instance)
        mock_detector.assert_called_once_with(mock_config_instance)


if __name__ == "__main__":
    unittest.main()
