"""
Sourdough Timelapse - Main Application
Monitors sourdough starter growth using Raspberry Pi camera and marker-based image processing
"""

import os
import sys
import yaml
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("Warning: picamera2 not available. Running in simulation mode.")

import cv2
import numpy as np

from marker_detector import MarkerDetector
from growth_monitor import GrowthMonitor


class SourdoughMonitor:
    """
    Main application for monitoring sourdough starter growth.
    """
    
    def __init__(self, config_path="config.yaml"):
        """
        Initialize the sourdough monitor.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
        
        # Initialize camera
        self.camera = None
        if PICAMERA_AVAILABLE:
            self.init_camera()
        
        # Initialize marker detector
        marker_config = self.config.get('marker', {})
        self.marker_detector = MarkerDetector(
            dictionary_name=marker_config.get('dictionary', 'DICT_4X4_50'),
            marker_size_mm=marker_config.get('marker_size_mm', 50)
        )
        
        # Initialize growth monitor
        growth_config = self.config.get('growth', {})
        self.growth_monitor = GrowthMonitor(growth_config)
        
        # Create output directory
        monitoring_config = self.config.get('monitoring', {})
        self.output_dir = Path(monitoring_config.get('output_dir', './captures'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitoring settings
        self.capture_interval = monitoring_config.get('capture_interval', 300)
        self.save_annotated = monitoring_config.get('save_annotated', True)
        self.reference_marker_id = marker_config.get('reference_marker_id', 0)
    
    def init_camera(self):
        """Initialize the Raspberry Pi camera."""
        camera_config = self.config.get('camera', {})
        
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={
                "size": (camera_config.get('width', 1920), 
                        camera_config.get('height', 1080)),
                "format": camera_config.get('format', 'RGB888')
            }
        )
        self.camera.configure(config)
        self.camera.start()
        
        # Allow camera to warm up
        time.sleep(2)
    
    def capture_image(self):
        """
        Capture an image from the camera.
        
        Returns:
            Captured image (numpy array)
        """
        if self.camera is not None:
            # Capture from Raspberry Pi camera
            image = self.camera.capture_array()
            # Convert RGB to BGR for OpenCV
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            # Simulation mode - create a dummy image
            print("Camera not available. Using dummy image.")
            image = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.putText(image, "Simulation Mode", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        return image
    
    def process_image(self, image):
        """
        Process an image to detect markers and measure culture growth.
        
        Args:
            image: Input image
            
        Returns:
            Tuple of (measurements, annotated_image, marker_info)
        """
        # Detect markers
        corners, ids, _ = self.marker_detector.detect_markers(image)
        marker_info = self.marker_detector.get_marker_info(corners, ids)
        
        # Get reference marker info if available
        reference_info = None
        if self.reference_marker_id in marker_info:
            reference_info = {self.reference_marker_id: marker_info[self.reference_marker_id]}
        
        # Analyze culture growth
        measurements, annotated = self.growth_monitor.analyze_image(image, reference_info)
        
        # Draw markers on annotated image
        if ids is not None:
            annotated = self.marker_detector.draw_markers(annotated, corners, ids)
        
        # Add marker info to measurements
        measurements['markers_detected'] = len(marker_info)
        measurements['marker_info'] = {}
        for k, v in marker_info.items():
            measurements['marker_info'][int(k)] = {
                'center': v.get('center', [0, 0]).tolist() if hasattr(v.get('center', [0, 0]), 'tolist') else v.get('center', [0, 0]),
                'size_pixels': float(v.get('size_pixels', 0)),
                'pixels_per_mm': float(v.get('pixels_per_mm', 1.0))
            }
        
        return measurements, annotated, marker_info
    
    def save_results(self, image, measurements, annotated, timestamp=None):
        """
        Save captured image and measurements.
        
        Args:
            image: Original captured image
            measurements: Measurements dictionary
            annotated: Annotated image with markers and measurements
            timestamp: Optional timestamp string (default: current time)
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save original image
            image_path = self.output_dir / f"capture_{timestamp}.jpg"
            cv2.imwrite(str(image_path), image)
            
            # Save annotated image if enabled
            if self.save_annotated:
                annotated_path = self.output_dir / f"annotated_{timestamp}.jpg"
                cv2.imwrite(str(annotated_path), annotated)
            
            # Save measurements as JSON
            measurements_path = self.output_dir / f"measurements_{timestamp}.json"
            with open(measurements_path, 'w') as f:
                json.dump(measurements, f, indent=2)
            
            print(f"Saved results to {self.output_dir}")
            print(f"  - Image: {image_path.name}")
            if self.save_annotated:
                print(f"  - Annotated: {annotated_path.name}")
            print(f"  - Measurements: {measurements_path.name}")
        except PermissionError:
            print(f"Error: Permission denied when writing to {self.output_dir}")
        except IOError as e:
            print(f"Error: Failed to save files: {e}")
        except Exception as e:
            print(f"Error: Unexpected error while saving results: {e}")
    
    def capture_and_analyze(self):
        """
        Capture and analyze a single image.
        
        Returns:
            Measurements dictionary
        """
        print(f"\n{datetime.now().isoformat()} - Capturing image...")
        
        # Capture image
        image = self.capture_image()
        
        # Process image
        measurements, annotated, marker_info = self.process_image(image)
        
        # Save results
        self.save_results(image, measurements, annotated)
        
        # Print summary
        print("\nAnalysis Results:")
        print(f"  Markers detected: {measurements.get('markers_detected', 0)}")
        if measurements.get('culture_detected'):
            print(f"  Culture detected: Yes")
            print(f"  Surface Y position: {measurements['surface_y_image']:.1f}px")
            print(f"  Height: {measurements['height_pixels']:.1f}px", end="")
            if measurements.get('height_mm') is not None:
                print(f" ({measurements['height_mm']:.1f}mm)")
            else:
                print(" (no calibration)")
        else:
            print(f"  Culture detected: No")
        
        return measurements
    
    def run_continuous(self):
        """
        Run continuous monitoring with periodic captures.
        """
        print(f"Starting continuous monitoring...")
        print(f"Capture interval: {self.capture_interval} seconds")
        print(f"Output directory: {self.output_dir}")
        print(f"Press Ctrl+C to stop")
        
        try:
            while True:
                self.capture_and_analyze()
                print(f"\nWaiting {self.capture_interval} seconds until next capture...")
                time.sleep(self.capture_interval)
        except KeyboardInterrupt:
            print("\n\nStopping monitoring...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.camera is not None:
            self.camera.stop()
            print("Camera stopped.")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Sourdough Starter Growth Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single capture
  python sourdough_monitor.py --single
  
  # Continuous monitoring (every 5 minutes by default)
  python sourdough_monitor.py --continuous
  
  # Generate a reference marker for printing
  python sourdough_monitor.py --generate-marker 0
        """
    )
    
    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--single', action='store_true',
                       help='Capture and analyze a single image')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    parser.add_argument('--generate-marker', type=int, metavar='ID',
                       help='Generate an ArUco marker image with the specified ID')
    
    args = parser.parse_args()
    
    # Generate marker mode
    if args.generate_marker is not None:
        try:
            # Load config just to get marker settings
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
            
            marker_config = config.get('marker', {})
            detector = MarkerDetector(
                dictionary_name=marker_config.get('dictionary', 'DICT_4X4_50'),
                marker_size_mm=marker_config.get('marker_size_mm', 50)
            )
            
            marker_image = detector.generate_marker(args.generate_marker, size_pixels=400)
            output_path = f"marker_{args.generate_marker}.png"
            cv2.imwrite(output_path, marker_image)
            print(f"Generated marker ID {args.generate_marker} -> {output_path}")
            print(f"Print this marker at {marker_config.get('marker_size_mm', 50)}mm x {marker_config.get('marker_size_mm', 50)}mm")
        except Exception as e:
            print(f"Error generating marker: {e}")
            sys.exit(1)
        return
    
    # Initialize monitor
    try:
        monitor = SourdoughMonitor(config_path=args.config)
    except Exception as e:
        print(f"Error initializing monitor: {e}")
        sys.exit(1)
    
    # Run requested mode
    try:
        if args.continuous:
            monitor.run_continuous()
        else:
            # Default to single capture
            monitor.capture_and_analyze()
            monitor.cleanup()
    except Exception as e:
        print(f"Error during monitoring: {e}")
        monitor.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
