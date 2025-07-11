"""
Screenshot Detection Module using computer vision and heuristics
"""

import cv2
import numpy as np
import logging
from typing import Tuple, List, Dict, Any
from io import BytesIO
from PIL import Image, ExifTags
import asyncio
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

logger = logging.getLogger(__name__)


class ScreenshotDetector:
    """Detects screenshots using various computer vision techniques"""

    def __init__(self, config):
        self.config = config
        self.confidence_threshold = config.screenshot_confidence_threshold
        self.max_image_size = config.max_image_size

    async def is_screenshot(self, image_data: bytes) -> bool:
        """
        Determine if an image is a screenshot using multiple detection methods

        Args:
            image_data: Raw image data as bytes

        Returns:
            bool: True if the image is likely a screenshot
        """
        if not image_data:
            return False

        try:
            # Load image
            image_io = BytesIO(image_data)
            try:
                image = Image.open(image_io)
            except Exception as e:
                logger.error(f"Failed to open image with PIL: {str(e)}")
                return False

            # Get image format
            image_format = image.format.lower() if image.format else ""
            logger.debug(f"Processing image of format: {image_format}")

            # Convert to RGB if needed
            if image.mode != "RGB":
                try:
                    image = image.convert("RGB")
                except Exception as e:
                    logger.error(f"Failed to convert image to RGB: {str(e)}")
                    return False

            # Resize if too large
            if max(image.size) > self.max_image_size:
                try:
                    image.thumbnail(
                        (self.max_image_size, self.max_image_size),
                        Image.Resampling.LANCZOS,
                    )
                except Exception as e:
                    logger.error(f"Failed to resize image: {str(e)}")
                    # Continue with original size if resize fails
                    pass

            try:
                # Convert to numpy array for OpenCV
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.error(f"Failed to convert image to OpenCV format: {str(e)}")
                return False

            # Run detection methods
            scores = await self._run_detection_methods(cv_image, image)

            # Calculate weighted confidence score
            final_score = self._calculate_final_score(scores)

            logger.debug(f"Screenshot detection scores: {scores}")
            logger.debug(f"Final confidence score: {final_score}")

            return final_score >= self.confidence_threshold

        except Exception as e:
            logger.error(f"Error in screenshot detection: {str(e)}")
            return False

    async def _run_detection_methods(
        self, cv_image: np.ndarray, pil_image: Image.Image
    ) -> Dict[str, float]:
        """Run all detection methods and return individual scores"""
        scores = {}

        # Method 1: Edge detection for UI elements
        scores["edge_density"] = self._detect_ui_edges(cv_image)

        # Method 2: Color histogram analysis
        scores["color_uniformity"] = self._analyze_color_distribution(cv_image)

        # Method 3: Text detection
        scores["text_density"] = self._detect_text_regions(cv_image)

        # Method 4: Geometric patterns (rectangles, buttons)
        scores["geometric_patterns"] = self._detect_geometric_patterns(cv_image)

        # Method 5: Aspect ratio analysis
        scores["aspect_ratio"] = self._analyze_aspect_ratio(cv_image)

        # Method 6: EXIF metadata analysis
        scores["metadata"] = self._analyze_metadata(pil_image)

        return scores

    def _detect_ui_edges(self, image: np.ndarray) -> float:
        """Detect UI elements through edge density analysis"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Calculate edge density
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])

            # Screenshots typically have moderate to high edge density
            if 0.05 <= edge_density <= 0.3:
                return min(edge_density * 3, 1.0)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error in UI edge detection: {str(e)}")
            return 0.0

    def _analyze_color_distribution(self, image: np.ndarray) -> float:
        """Analyze color distribution for screenshot characteristics"""
        try:
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Calculate histogram for each channel
            hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])

            # Screenshots often have:
            # - Limited color palette (spikes in histograms)
            # - High value (brightness) for white backgrounds
            # - Low saturation for UI elements

            # Check for color palette limitation
            color_peaks = len([x for x in hist_h.flatten() if x > np.max(hist_h) * 0.1])
            color_score = min(1.0, (50 - color_peaks) / 50) if color_peaks < 50 else 0.0

            # Check for high brightness
            brightness_score = np.sum(hist_v[200:]) / np.sum(hist_v)

            # Check for low saturation
            low_sat_score = np.sum(hist_s[:100]) / np.sum(hist_s)

            return (color_score + brightness_score + low_sat_score) / 3

        except Exception as e:
            logger.error(f"Error in color distribution analysis: {str(e)}")
            return 0.0

    def _detect_text_regions(self, image: np.ndarray) -> float:
        """Detect text regions that are common in screenshots"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Use morphological operations to find text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

            # Apply threshold
            _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find text-like regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(
                connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Filter contours that look like text
            text_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                area = cv2.contourArea(contour)

                # Text characteristics: appropriate aspect ratio and size
                if 1.5 <= aspect_ratio <= 15 and 50 <= area <= 5000:
                    text_contours.append(contour)

            # Calculate text density
            text_area = sum(cv2.contourArea(contour) for contour in text_contours)
            total_area = gray.shape[0] * gray.shape[1]
            text_density = text_area / total_area

            # Screenshots typically have moderate text density
            return min(text_density * 10, 1.0)

        except Exception as e:
            logger.error(f"Error in text detection: {str(e)}")
            return 0.0

    def _detect_geometric_patterns(self, image: np.ndarray) -> float:
        """Detect geometric patterns like rectangles and buttons"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Edge detection
            edges = cv2.Canny(gray, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Count rectangular shapes
            rectangles = 0
            for contour in contours:
                # Approximate the contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Check if it's a rectangle
                if len(approx) == 4:
                    area = cv2.contourArea(contour)
                    if area > 100:  # Minimum area threshold
                        rectangles += 1

            # Normalize by image size
            total_area = gray.shape[0] * gray.shape[1]
            rectangle_density = rectangles / (total_area / 10000)  # Per 10k pixels

            return min(rectangle_density / 5, 1.0)

        except Exception as e:
            logger.error(f"Error in geometric pattern detection: {str(e)}")
            return 0.0

    def _analyze_aspect_ratio(self, image: np.ndarray) -> float:
        """Analyze aspect ratio for common screenshot dimensions"""
        try:
            height, width = image.shape[:2]
            aspect_ratio = width / height

            # Common screenshot aspect ratios
            common_ratios = [
                16 / 9,  # 1920x1080, 2560x1440
                16 / 10,  # 1920x1200, 2560x1600
                4 / 3,  # 1024x768, 1600x1200
                3 / 2,  # 1440x960
                21 / 9,  # Ultra-wide
                9 / 16,  # Mobile portrait
                10 / 16,  # Mobile portrait
            ]

            # Find closest match
            closest_diff = min(abs(aspect_ratio - ratio) for ratio in common_ratios)

            # Score based on how close to common ratios
            if closest_diff < 0.1:
                return 0.8
            elif closest_diff < 0.2:
                return 0.6
            elif closest_diff < 0.3:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            logger.error(f"Error in aspect ratio analysis: {str(e)}")
            return 0.0

    def _analyze_metadata(self, image: Image.Image) -> float:
        """Analyze EXIF metadata for screenshot indicators"""
        try:
            exif_data = image._getexif()
            if not exif_data:
                return 0.0

            # Convert EXIF data to readable format
            exif = {}
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                exif[tag] = value

            # Check for screenshot indicators
            score = 0.0

            # No camera manufacturer (screenshots don't have camera EXIF)
            if "Make" not in exif and "Model" not in exif:
                score += 0.3

            # Check software field for screenshot tools
            software = exif.get("Software", "").lower()
            screenshot_software = [
                "screenshot",
                "snip",
                "grab",
                "capture",
                "scrot",
                "maim",
                "lightshot",
                "gyazo",
                "puush",
                "flameshot",
                "spectacle",
            ]

            if any(tool in software for tool in screenshot_software):
                score += 0.7

            # Check for lack of camera settings
            camera_tags = ["FNumber", "ExposureTime", "ISOSpeedRatings", "FocalLength"]
            missing_camera_tags = sum(1 for tag in camera_tags if tag not in exif)
            score += (missing_camera_tags / len(camera_tags)) * 0.3

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error in metadata analysis: {str(e)}")
            return 0.0

    def _calculate_final_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted final confidence score"""
        # Weights for different detection methods
        weights = {
            "edge_density": 0.2,
            "color_uniformity": 0.15,
            "text_density": 0.25,
            "geometric_patterns": 0.2,
            "aspect_ratio": 0.1,
            "metadata": 0.1,
        }

        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0

        for method, score in scores.items():
            if method in weights:
                weight = weights[method]
                weighted_sum += score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight
