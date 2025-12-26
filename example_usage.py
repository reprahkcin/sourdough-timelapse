#!/usr/bin/env python3
"""
Example usage script for the sourdough monitoring system.
Demonstrates the main features and typical workflows.
"""

import os
import sys

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60 + "\n")

def main():
    print_header("Sourdough Timelapse Monitor - Example Usage")
    
    print("This script demonstrates how to use the sourdough monitoring system.\n")
    
    print("1. GENERATE A MARKER FOR PRINTING")
    print("-" * 60)
    print("First, generate an ArUco marker to use as a reference:")
    print("  $ python3 sourdough_monitor.py --generate-marker 0")
    print("\nThis creates 'marker_0.png' that you should print at exactly 50mm x 50mm.")
    print("Place this marker at a fixed position in your camera's view.\n")
    
    print("2. SINGLE CAPTURE AND ANALYSIS")
    print("-" * 60)
    print("Take a single photo and analyze it:")
    print("  $ python3 sourdough_monitor.py --single")
    print("\nThis will:")
    print("  - Capture an image from the Raspberry Pi camera")
    print("  - Detect ArUco markers in the image")
    print("  - Measure the culture height using image processing")
    print("  - Save results to the 'captures' directory\n")
    
    print("3. CONTINUOUS MONITORING (TIMELAPSE)")
    print("-" * 60)
    print("Run continuous monitoring with periodic captures:")
    print("  $ python3 sourdough_monitor.py --continuous")
    print("\nBy default, this captures every 5 minutes (configurable in config.yaml).")
    print("Press Ctrl+C to stop monitoring.\n")
    
    print("4. CUSTOM CONFIGURATION")
    print("-" * 60)
    print("Create a custom config file and use it:")
    print("  $ cp config.yaml my_config.yaml")
    print("  # Edit my_config.yaml with your settings")
    print("  $ python3 sourdough_monitor.py --config my_config.yaml --continuous\n")
    
    print("5. VIEW RESULTS")
    print("-" * 60)
    print("Check the captures directory for results:")
    print("  $ ls -lh captures/")
    print("\nEach capture produces:")
    print("  - capture_TIMESTAMP.jpg    (original image)")
    print("  - annotated_TIMESTAMP.jpg  (with markers and measurements)")
    print("  - measurements_TIMESTAMP.json (detailed data)\n")
    
    print("6. CREATE TIMELAPSE VIDEO")
    print("-" * 60)
    print("After collecting images, create a timelapse video:")
    print("  $ ffmpeg -framerate 30 -pattern_type glob -i 'captures/annotated_*.jpg' \\")
    print("           -c:v libx264 -pix_fmt yuv420p timelapse.mp4\n")
    
    print("7. RUN TEST SCRIPT")
    print("-" * 60)
    print("Test the system with synthetic images:")
    print("  $ python3 test_monitor.py")
    print("\nThis creates test images in /tmp/ to verify the system works.\n")
    
    print_header("Configuration Tips")
    
    print("Edit config.yaml to adjust:")
    print("  - Camera resolution and format")
    print("  - Marker size (must match your printed marker!)")
    print("  - Capture interval for timelapse")
    print("  - Region of interest (ROI) for culture detection")
    print("  - Edge detection sensitivity\n")
    
    print("For more information, see README.md")
    print()

if __name__ == "__main__":
    main()
