# Setup

## ilastik Training

1. Create a new ilastik project (ilp) for the AutoContext (2-stage) workflow.
2. Convert your single tif training images to 8-bit in FIJI/ImageJ.
3. Import images in the 'Input Data' section under `raw data`:
   - Select all images, right-click, edit properties.
   - Change 'Storage' from 'Relative Link' to 'Copied to Project File'.
4. Stage 1: Label all classifiers equally, targeting irregular shapes and uncertain areas.
5. Stage 2: Label more freely, focusing on areas of uncertainty from Stage 1.

## Workflow Setup

1. Open terminal and `cd /Users/Italiano/Desktop/Italiano_MK_Analysis`.
2. Run: `pipenv install -r requirements.txt`
3. Edit config.ini:
   - Update file paths for your OS (Darwin - Mac, Win32 - Windows, Linux).