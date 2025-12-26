"""
Culture Growth Monitor Module
Analyzes images to detect and measure sourdough culture growth
"""

import cv2
import numpy as np
from datetime import datetime


class GrowthMonitor:
    """
    Monitors sourdough culture growth using image processing.
    """
    
    def __init__(self, config):
        """
        Initialize the growth monitor.
        
        Args:
            config: Configuration dictionary with growth monitoring parameters
        """
        self.config = config
        self.roi_x_start = config.get('roi_x_start', 0.3)
        self.roi_x_end = config.get('roi_x_end', 0.7)
        self.roi_y_start = config.get('roi_y_start', 0.2)
        self.roi_y_end = config.get('roi_y_end', 0.9)
        self.edge_threshold1 = config.get('edge_threshold1', 50)
        self.edge_threshold2 = config.get('edge_threshold2', 150)
        self.min_contour_area = config.get('min_contour_area', 1000)
    
    def get_roi(self, image):
        """
        Extract region of interest from the image.
        
        Args:
            image: Input image
            
        Returns:
            ROI image and coordinates (x1, y1, x2, y2)
        """
        h, w = image.shape[:2]
        
        x1 = int(w * self.roi_x_start)
        x2 = int(w * self.roi_x_end)
        y1 = int(h * self.roi_y_start)
        y2 = int(h * self.roi_y_end)
        
        roi = image[y1:y2, x1:x2]
        
        return roi, (x1, y1, x2, y2)
    
    def detect_culture_surface(self, image, marker_info=None):
        """
        Detect the surface level of the sourdough culture.
        
        Args:
            image: Input image
            marker_info: Optional marker information for calibration
            
        Returns:
            Dictionary with culture measurements
        """
        # Get ROI
        roi, (x1, y1, x2, y2) = self.get_roi(image)
        
        # Convert to grayscale
        if len(roi.shape) == 3:
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray_roi = roi
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, self.edge_threshold1, self.edge_threshold2)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        valid_contours = [c for c in contours if cv2.contourArea(c) > self.min_contour_area]
        
        measurements = {
            'timestamp': datetime.now().isoformat(),
            'culture_detected': False,
            'surface_y_roi': None,
            'surface_y_image': None,
            'height_pixels': None,
            'height_mm': None,
            'contour_count': len(valid_contours)
        }
        
        if valid_contours:
            # Find the topmost point across all contours (culture surface)
            min_y = float('inf')
            max_y = float('-inf')
            
            for contour in valid_contours:
                contour_min_y = np.min(contour[:, 0, 1])
                contour_max_y = np.max(contour[:, 0, 1])
                min_y = min(min_y, contour_min_y)
                max_y = max(max_y, contour_max_y)
            
            # Culture height in ROI coordinates
            height_roi = max_y - min_y
            
            # Convert to image coordinates
            surface_y_image = y1 + min_y
            height_image = height_roi
            
            measurements['culture_detected'] = True
            measurements['surface_y_roi'] = float(min_y)
            measurements['surface_y_image'] = float(surface_y_image)
            measurements['height_pixels'] = float(height_image)
            
            # Convert to mm if marker calibration is available
            if marker_info:
                # Use the first available marker for calibration
                for marker_id, info in marker_info.items():
                    pixels_per_mm = info.get('pixels_per_mm', 1.0)
                    measurements['height_mm'] = float(height_image / pixels_per_mm)
                    measurements['calibration_marker_id'] = int(marker_id)
                    break
        
        return measurements
    
    def draw_measurements(self, image, measurements, roi_coords=None):
        """
        Draw culture measurements on the image.
        
        Args:
            image: Input image
            measurements: Measurements dictionary from detect_culture_surface
            roi_coords: Optional ROI coordinates to draw
            
        Returns:
            Annotated image
        """
        output = image.copy()
        
        # Draw ROI rectangle if provided
        if roi_coords:
            x1, y1, x2, y2 = roi_coords
            cv2.rectangle(output, (x1, y1), (x2, y2), (255, 255, 0), 2)
            cv2.putText(output, "ROI", (x1 + 5, y1 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw culture surface line
        if measurements.get('culture_detected') and measurements.get('surface_y_image') is not None:
            surface_y = int(measurements['surface_y_image'])
            cv2.line(output, (0, surface_y), (image.shape[1], surface_y), (0, 255, 0), 2)
            
            # Add measurement text
            height_text = f"Height: {measurements['height_pixels']:.1f}px"
            if measurements.get('height_mm') is not None:
                height_text += f" ({measurements['height_mm']:.1f}mm)"
            
            cv2.putText(output, height_text, (10, surface_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Add timestamp
        timestamp = measurements.get('timestamp', datetime.now().isoformat())
        cv2.putText(output, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return output
    
    def analyze_image(self, image, marker_info=None):
        """
        Complete analysis of an image for culture growth.
        
        Args:
            image: Input image
            marker_info: Optional marker information for calibration
            
        Returns:
            Tuple of (measurements, annotated_image)
        """
        # Get ROI coordinates
        _, roi_coords = self.get_roi(image)
        
        # Detect culture surface
        measurements = self.detect_culture_surface(image, marker_info)
        
        # Create annotated image
        annotated = self.draw_measurements(image, measurements, roi_coords)
        
        return measurements, annotated
