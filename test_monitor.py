"""
Test script for sourdough monitoring system
Creates a synthetic test image with a marker and simulated culture
"""

import cv2
import numpy as np
from marker_detector import MarkerDetector
from growth_monitor import GrowthMonitor
import yaml

def create_test_image():
    """Create a test image with a marker and simulated culture."""
    # Create blank image (simulating a photo of a jar)
    width, height = 1920, 1080
    image = np.ones((height, width, 3), dtype=np.uint8) * 240  # Light gray background
    
    # Draw a jar outline
    jar_center_x = width // 2
    jar_bottom = height - 100
    jar_top = 200
    jar_width = 400
    jar_left = jar_center_x - jar_width // 2
    jar_right = jar_center_x + jar_width // 2
    
    # Draw jar sides
    cv2.line(image, (jar_left, jar_top), (jar_left, jar_bottom), (100, 100, 100), 3)
    cv2.line(image, (jar_right, jar_top), (jar_right, jar_bottom), (100, 100, 100), 3)
    cv2.line(image, (jar_left, jar_bottom), (jar_right, jar_bottom), (100, 100, 100), 3)
    
    # Fill jar with lighter color
    cv2.rectangle(image, (jar_left + 3, jar_top), (jar_right - 3, jar_bottom - 3), (220, 220, 220), -1)
    
    # Draw simulated culture (darker region in bottom part of jar)
    culture_height = 300
    culture_top = jar_bottom - culture_height
    cv2.rectangle(image, (jar_left + 3, culture_top), (jar_right - 3, jar_bottom - 3), (180, 160, 140), -1)
    
    # Add some texture to the culture surface
    culture_surface_noise = np.random.randint(-20, 20, size=(10, jar_width - 6))
    for i in range(10):
        for j in range(jar_width - 6):
            y = culture_top + i
            x = jar_left + 3 + j
            if 0 <= y < height and 0 <= x < width:
                image[y, x] = np.clip(image[y, x] + culture_surface_noise[i, j], 0, 255)
    
    # Generate and place an ArUco marker at the bottom
    marker_detector = MarkerDetector(dictionary_name="DICT_4X4_50", marker_size_mm=50)
    marker_image = marker_detector.generate_marker(0, size_pixels=200)
    
    # Convert marker to BGR
    marker_bgr = cv2.cvtColor(marker_image, cv2.COLOR_GRAY2BGR)
    
    # Place marker at bottom center (ensure it fits)
    marker_x = jar_center_x - 100
    marker_y = min(jar_bottom + 30, height - 220)  # Leave room for marker
    
    # Add white border around marker for better visibility
    border_size = 10
    if marker_y + 200 + border_size <= height and marker_x + 200 + border_size <= width:
        image[marker_y - border_size:marker_y + 200 + border_size, 
              marker_x - border_size:marker_x + 200 + border_size] = 255
        
        # Place the marker
        image[marker_y:marker_y + 200, marker_x:marker_x + 200] = marker_bgr
    
    return image


def test_marker_detection():
    """Test marker detection on synthetic image."""
    print("=" * 60)
    print("Testing Marker Detection")
    print("=" * 60)
    
    # Create test image
    image = create_test_image()
    
    # Initialize detector
    detector = MarkerDetector(dictionary_name="DICT_4X4_50", marker_size_mm=50)
    
    # Detect markers
    corners, ids, rejected = detector.detect_markers(image)
    
    if ids is not None:
        print(f"✓ Detected {len(ids)} marker(s)")
        marker_info = detector.get_marker_info(corners, ids)
        
        for marker_id, info in marker_info.items():
            print(f"\nMarker ID {marker_id}:")
            print(f"  Center: {info['center']}")
            print(f"  Size (pixels): {info['size_pixels']:.2f}")
            print(f"  Pixels per mm: {info['pixels_per_mm']:.2f}")
    else:
        print("✗ No markers detected")
    
    # Save test image with markers drawn
    annotated = detector.draw_markers(image, corners, ids)
    cv2.imwrite('/tmp/test_marker_detection.jpg', annotated)
    print(f"\n✓ Saved annotated image to /tmp/test_marker_detection.jpg")
    
    return image, corners, ids


def test_growth_monitoring():
    """Test growth monitoring on synthetic image."""
    print("\n" + "=" * 60)
    print("Testing Growth Monitoring")
    print("=" * 60)
    
    # Create test image
    image = create_test_image()
    
    # Initialize components
    detector = MarkerDetector(dictionary_name="DICT_4X4_50", marker_size_mm=50)
    
    # Load config for growth monitor
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    growth_config = config.get('growth', {})
    monitor = GrowthMonitor(growth_config)
    
    # Detect markers for calibration
    corners, ids, _ = detector.detect_markers(image)
    marker_info = detector.get_marker_info(corners, ids)
    
    # Analyze growth
    measurements, annotated = monitor.analyze_image(image, marker_info)
    
    # Draw markers on annotated image
    if ids is not None:
        annotated = detector.draw_markers(annotated, corners, ids)
    
    # Print results
    print(f"Culture detected: {measurements.get('culture_detected', False)}")
    if measurements.get('culture_detected'):
        print(f"Surface Y position: {measurements['surface_y_image']:.1f} pixels")
        print(f"Height: {measurements['height_pixels']:.1f} pixels", end="")
        if measurements.get('height_mm') is not None:
            print(f" ({measurements['height_mm']:.1f} mm)")
        else:
            print()
    
    # Save annotated image
    cv2.imwrite('/tmp/test_growth_monitoring.jpg', annotated)
    print(f"\n✓ Saved annotated image to /tmp/test_growth_monitoring.jpg")
    
    return measurements


def test_full_pipeline():
    """Test the full monitoring pipeline."""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline")
    print("=" * 60)
    
    # Create test image
    image = create_test_image()
    
    # Save original test image
    cv2.imwrite('/tmp/test_original.jpg', image)
    print(f"✓ Created synthetic test image: /tmp/test_original.jpg")
    
    # Run marker detection test
    test_image, corners, ids = test_marker_detection()
    
    # Run growth monitoring test
    measurements = test_growth_monitoring()
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    print("\nGenerated test images:")
    print("  - /tmp/test_original.jpg (synthetic test image)")
    print("  - /tmp/test_marker_detection.jpg (with markers highlighted)")
    print("  - /tmp/test_growth_monitoring.jpg (with full analysis)")


if __name__ == "__main__":
    test_full_pipeline()
