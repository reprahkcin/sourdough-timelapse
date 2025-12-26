"""
ArUco Marker Detection Module
Detects and tracks ArUco markers in images for reference point tracking
"""

import cv2
import numpy as np


class MarkerDetector:
    """
    Detects ArUco markers in images and provides reference measurements.
    """
    
    def __init__(self, dictionary_name="DICT_4X4_50", marker_size_mm=50):
        """
        Initialize the marker detector.
        
        Args:
            dictionary_name: Name of the ArUco dictionary to use
            marker_size_mm: Physical size of the marker in millimeters
        """
        self.marker_size_mm = marker_size_mm
        
        # Get the ArUco dictionary
        aruco_dict_map = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
            "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
            "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
        }
        
        dict_id = aruco_dict_map.get(dictionary_name, cv2.aruco.DICT_4X4_50)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(dict_id)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
    
    def detect_markers(self, image):
        """
        Detect ArUco markers in the image.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Tuple of (corners, ids, rejected) from ArUco detection
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        return corners, ids, rejected
    
    def get_marker_info(self, corners, ids, target_id=None):
        """
        Get information about detected markers.
        
        Args:
            corners: Marker corners from detection
            ids: Marker IDs from detection
            target_id: Specific marker ID to get info for (None = all markers)
            
        Returns:
            Dictionary with marker information (center, corners, size in pixels)
        """
        if ids is None or len(ids) == 0:
            return {}
        
        marker_info = {}
        
        for i, marker_id in enumerate(ids.flatten()):
            if target_id is not None and marker_id != target_id:
                continue
            
            # Get corners for this marker
            corner_points = corners[i][0]
            
            # Calculate center
            center = np.mean(corner_points, axis=0)
            
            # Calculate marker size in pixels (average of all sides)
            side_lengths = []
            for j in range(4):
                p1 = corner_points[j]
                p2 = corner_points[(j + 1) % 4]
                length = np.linalg.norm(p2 - p1)
                side_lengths.append(length)
            
            avg_size_pixels = np.mean(side_lengths)
            
            marker_info[marker_id] = {
                'center': center,
                'corners': corner_points,
                'size_pixels': avg_size_pixels,
                'pixels_per_mm': avg_size_pixels / self.marker_size_mm if self.marker_size_mm > 0 else 1.0
            }
        
        return marker_info
    
    def draw_markers(self, image, corners, ids):
        """
        Draw detected markers on the image.
        
        Args:
            image: Input image to draw on
            corners: Marker corners from detection
            ids: Marker IDs from detection
            
        Returns:
            Image with markers drawn
        """
        output = image.copy()
        
        if ids is not None and len(ids) > 0:
            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(output, corners, ids)
        
        return output
    
    def generate_marker(self, marker_id, size_pixels=200):
        """
        Generate an ArUco marker image for printing.
        
        Args:
            marker_id: ID of the marker to generate
            size_pixels: Size of the output image in pixels
            
        Returns:
            Marker image
        """
        marker_image = cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, size_pixels)
        return marker_image
