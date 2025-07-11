"""
Basic tests for the Immich Screenshot Categorizer
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestBasicImports(unittest.TestCase):
    """Test that all modules can be imported correctly"""

    def test_config_import(self):
        """Test that config module can be imported"""
        from src.config import Config

        self.assertTrue(hasattr(Config, "__init__"))

    def test_immich_client_import(self):
        """Test that immich_client module can be imported"""
        from src.immich_client import ImmichClient

        self.assertTrue(hasattr(ImmichClient, "__init__"))

    def test_screenshot_detector_import(self):
        """Test that screenshot_detector module can be imported"""
        from src.screenshot_detector import ScreenshotDetector

        self.assertTrue(hasattr(ScreenshotDetector, "__init__"))


class TestConfigModule(unittest.TestCase):
    """Test the configuration module"""

    def setUp(self):
        """Set up test environment"""
        self.env_vars = {
            "IMMICH_API_KEY": "test-api-key",
            "IMMICH_USER_ID": "test-user-id",
            "IMMICH_SERVER_URL": "http://localhost:3001",
        }

    @patch.dict(
        os.environ, {"IMMICH_API_KEY": "test-key", "IMMICH_USER_ID": "test-user"}
    )
    def test_config_creation(self):
        """Test that Config can be created with required environment variables"""
        from src.config import Config

        config = Config()
        self.assertEqual(config.immich_api_key, "test-key")
        self.assertEqual(config.immich_user_id, "test-user")

    @patch.dict(os.environ, {}, clear=True)
    def test_config_missing_required_vars(self):
        """Test that Config raises error when required vars are missing"""
        from src.config import Config

        with self.assertRaises(ValueError):
            Config()


class TestImmichClient(unittest.TestCase):
    """Test the Immich client"""

    def setUp(self):
        """Set up test environment"""
        self.mock_config = Mock()
        self.mock_config.immich_server_url = "http://localhost:3001"
        self.mock_config.immich_api_key = "test-key"
        self.mock_config.immich_user_id = "test-user"
        self.mock_config.screenshot_tag = "screenshot"
        self.mock_config.create_album = True
        self.mock_config.album_name = "Screenshots"

    def test_immich_client_creation(self):
        """Test that ImmichClient can be created"""
        from src.immich_client import ImmichClient

        client = ImmichClient(self.mock_config)
        self.assertEqual(client.base_url, "http://localhost:3001")
        self.assertEqual(client.api_key, "test-key")


class TestScreenshotDetector(unittest.TestCase):
    """Test the screenshot detector"""

    def setUp(self):
        """Set up test environment"""
        self.mock_config = Mock()
        self.mock_config.screenshot_confidence_threshold = 0.7
        self.mock_config.max_image_size = 2048

    def test_screenshot_detector_creation(self):
        """Test that ScreenshotDetector can be created"""
        from src.screenshot_detector import ScreenshotDetector

        detector = ScreenshotDetector(self.mock_config)
        self.assertEqual(detector.confidence_threshold, 0.7)
        self.assertEqual(detector.max_image_size, 2048)


class TestMainApplication(unittest.TestCase):
    """Test the main application"""

    @patch("main.Config")
    @patch("main.ImmichClient")
    @patch("main.ScreenshotDetector")
    def test_main_application_creation(self, mock_detector, mock_client, mock_config):
        """Test that the main application can be created"""
        # Import after patching
        from main import ImmichScreenshotCategorizer

        # Create mocks
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance

        # Create application
        app = ImmichScreenshotCategorizer(mock_config_instance)

        # Verify
        self.assertIsNotNone(app)
        self.assertEqual(app.config, mock_config_instance)
        mock_client.assert_called_once_with(mock_config_instance)
        mock_detector.assert_called_once_with(mock_config_instance)


if __name__ == "__main__":
    unittest.main()
