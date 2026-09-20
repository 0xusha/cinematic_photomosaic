# Cinematic Photomosaic Loop

A Python script that generates a continuous, fullscreen animated photomosaic. It disassembles a source image into tiles, animates their flight into a grid, performs a smooth sub-pixel zoom into the high-resolution original, and disperses the tiles to seamlessly restart the loop.

## Requirements

* Python 3.x
* OpenCV (`pip install opencv-python`)
* NumPy (`pip install numpy`)

## Usage

1. **Provide Your Own Image:** This repository does not include a default image. You must add your own photo to the project folder and name it `image.png`.
2. Run the script from your terminal:
   ```bash
   python cinematic_photomosaic.py


   Press the Esc key at any time to exit the fullscreen animation.

Configuration
You can adjust the number of tiles by modifying the parameters at the bottom of the script:

Python
run_photomosaic_experience('image.png', grid_cols=70, grid_rows=70)
