# Sourdough Timelapse Monitor

An app for tracking, documenting and managing sourdough starter jars using Raspberry Pi and standard v2 camera. Uses ArUco marker system and image processing to monitor culture growth automatically.

## Features

- **Automated Image Capture**: Uses Raspberry Pi Camera v2 for high-quality images
- **Marker-Based Calibration**: ArUco markers provide reference points for accurate measurements
- **Growth Tracking**: Advanced image processing to detect and measure culture height
- **Timelapse Ready**: Periodic captures suitable for creating timelapse videos
- **Real Measurements**: Convert pixel measurements to millimeters using marker calibration
- **Annotated Output**: Visual feedback showing detected markers and measurements

## Hardware Requirements

- Raspberry Pi (3, 4, or 5 recommended)
- Raspberry Pi Camera Module v2
- Printed ArUco marker (template can be generated with the tool)
- Jar or container for sourdough starter
- Stable mounting for camera pointing at the jar

## Installation

### On Raspberry Pi

1. **Clone the repository**:
```bash
git clone https://github.com/reprahkcin/sourdough-timelapse.git
cd sourdough-timelapse
```

2. **Install system dependencies**:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv
```

3. **Install Python dependencies**:
```bash
pip3 install -r requirements.txt
```

4. **Enable camera**:
```bash
sudo raspi-config
# Navigate to Interface Options -> Camera -> Enable
```

## Setup

### 1. Generate and Print Marker

Generate an ArUco marker to use as a reference:

```bash
python3 sourdough_monitor.py --generate-marker 0
```

This creates `marker_0.png`. Print this marker at exactly **50mm x 50mm** (or whatever size you configure in `config.yaml`). The physical size must match the configuration for accurate measurements.

### 2. Position the Marker

Place the printed marker at a fixed position in the camera view, preferably:
- At the bottom of the jar or on the surface below it
- Clearly visible and well-lit
- Flat and perpendicular to the camera

### 3. Configure Settings

Edit `config.yaml` to adjust:
- Camera resolution and format
- Marker size (must match printed size!)
- Capture interval for timelapse
- Region of interest for culture detection
- Edge detection sensitivity

## Usage

### Single Capture and Analysis

Take a single photo and analyze it:

```bash
python3 sourdough_monitor.py --single
```

This will:
1. Capture an image from the camera
2. Detect ArUco markers
3. Measure culture height
4. Save original image, annotated image, and measurements to `./captures/`

### Continuous Monitoring (Timelapse)

Run continuous monitoring with automatic periodic captures:

```bash
python3 sourdough_monitor.py --continuous
```

By default, this captures an image every 5 minutes (configurable in `config.yaml`). Press Ctrl+C to stop.

### Custom Configuration

Use a different configuration file:

```bash
python3 sourdough_monitor.py --config my_config.yaml --continuous
```

## Output

Each capture produces three files in the output directory:

1. **capture_TIMESTAMP.jpg**: Original camera image
2. **annotated_TIMESTAMP.jpg**: Image with markers, ROI, and measurements drawn
3. **measurements_TIMESTAMP.json**: Detailed measurements including:
   - Timestamp
   - Culture detection status
   - Surface position (pixels)
   - Height in pixels and millimeters
   - Marker information

Example measurements JSON:
```json
{
  "timestamp": "2025-12-26T18:20:00.123456",
  "culture_detected": true,
  "surface_y_image": 456.3,
  "height_pixels": 234.5,
  "height_mm": 47.8,
  "markers_detected": 1,
  "marker_info": {
    "0": {
      "center": [960.5, 890.2],
      "size_pixels": 245.6,
      "pixels_per_mm": 4.912
    }
  }
}
```

## How It Works

### Marker Detection

The system uses **ArUco markers** - a type of fiducial marker commonly used in computer vision. These markers:
- Are easily and reliably detected by OpenCV
- Provide precise position information
- Can be used for scale calibration (converting pixels to real-world measurements)
- Work well in varying lighting conditions

### Growth Monitoring

The culture growth detection works by:

1. **Region of Interest (ROI)**: Focuses on a specific area where the jar is located
2. **Edge Detection**: Uses Canny edge detection to find boundaries
3. **Contour Analysis**: Identifies contours that likely represent the culture surface
4. **Surface Detection**: Finds the topmost edge as the culture surface
5. **Height Calculation**: Measures from bottom to top of detected culture
6. **Calibration**: Converts pixel measurements to millimeters using marker size

### Measurement Accuracy

Accuracy depends on:
- **Marker size accuracy**: Print the marker at exactly the configured size
- **Camera position**: Keep camera fixed and perpendicular to the jar
- **Lighting**: Consistent, even lighting improves edge detection
- **Jar position**: Keep jar in the same position for all captures

## Configuration Reference

See `config.yaml` for all available options:

```yaml
camera:
  width: 1920              # Camera resolution width
  height: 1080             # Camera resolution height
  format: "RGB888"         # Image format

marker:
  dictionary: "DICT_4X4_50"    # ArUco dictionary type
  marker_size_mm: 50           # Physical marker size (must match printed size!)
  reference_marker_id: 0       # Marker ID to use for calibration

monitoring:
  capture_interval: 300        # Seconds between captures (5 minutes)
  output_dir: "./captures"     # Where to save images and data
  save_annotated: true         # Save images with annotations

growth:
  roi_x_start: 0.3        # ROI left edge (30% from left)
  roi_x_end: 0.7          # ROI right edge (70% from left)
  roi_y_start: 0.2        # ROI top edge (20% from top)
  roi_y_end: 0.9          # ROI bottom edge (90% from top)
  edge_threshold1: 50     # Canny edge detection lower threshold
  edge_threshold2: 150    # Canny edge detection upper threshold
  min_contour_area: 1000  # Minimum contour size to consider
```

## Troubleshooting

### Camera Not Found
- Run `sudo raspi-config` and enable the camera interface
- Reboot after enabling: `sudo reboot`
- Check camera connection

### Markers Not Detected
- Ensure marker is well-lit and clearly visible
- Check that marker is flat and not distorted
- Verify marker ID matches configuration
- Try adjusting camera position or lighting

### Inaccurate Measurements
- Verify printed marker size matches configuration exactly
- Ensure camera and jar remain in fixed positions
- Check that marker is perpendicular to camera
- Adjust ROI settings to focus on jar area

### Poor Culture Detection
- Adjust `edge_threshold1` and `edge_threshold2` in config
- Modify ROI settings to better frame the jar
- Ensure good contrast between culture and jar/background
- Adjust `min_contour_area` to filter noise

## Creating Timelapse Videos

After collecting images, create a timelapse video using ffmpeg:

```bash
# Install ffmpeg if needed
sudo apt-get install ffmpeg

# Create timelapse from annotated images (30 fps)
ffmpeg -framerate 30 -pattern_type glob -i 'captures/annotated_*.jpg' \
  -c:v libx264 -pix_fmt yuv420p timelapse.mp4
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

## Acknowledgments

- Uses OpenCV for image processing and ArUco marker detection
- Built for Raspberry Pi using picamera2