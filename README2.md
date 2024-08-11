# MK Analysis

## Getting Started

This image processing workflow analyzes phase-contrast, tif time-lapses of Megakaryocytes & Pro-platelet differentiation using ilastik & CellProfiler.

## Prerequisites

### Image Formats

- **Multi-Image Stack (.tif)**: Stacks should be in a folder, named: *Date_ExperimentName_Well_Site* (e.g. 190101_MK_A1_1).
- **Single 8-bit Images (.tif)**: Individual images should be in a folder named *single_images*.

### Required Software

- Italiano_MK_Analysis Repository
- Python 3
- ilastik
- CellProfiler & CellProfiler Analyst (Java Runtime Environment required)

## Installation

### Italiano_MK_Analysis Repository

1. Clone/download this Github repository.
2. Move/unzip the repo into your home folder (e.g. /home/Italiano [Mac]; C:\Users\Italiano\ [Windows]).

### Python 3

1. Download and install Python 3 from https://www.python.org/downloads/
2. Open a terminal/command prompt.
3. Run: `pip3 install pipenv`

### ilastik

Download from https://www.ilastik.org/download.html
- Mac: Unpack the tar.bz2 file, move the ilastik icon to Applications folder.
- Windows: Run the default installation.

### CellProfiler

Download from https://cellprofiler.org/releases/
- Mac: Unzip the file, move the CellProfiler icon to Applications folder.
- Windows: Run the default installation.

## Setup

### ilastik Training

1. Create a new ilastik project (ilp) for the AutoContext (2-stage) workflow.
2. Convert training images to 8-bit in FIJI/ImageJ.
3. Import images in 'Input Data' section:
   - Select all images, right-click, edit properties.
   - Change 'Storage' from 'Relative Link' to 'Copied to Project File'.
4. Stage 1: Label all classifiers equally, targeting irregular shapes and uncertain areas.
5. Stage 2: Label more freely, focusing on areas of uncertainty from Stage 1.

### Workflow Setup

1. Open terminal, navigate to Italiano_MK_Analysis folder.
2. Run: `pipenv install -r requirements.txt`
3. Edit config.ini:
   - Update file paths for your OS (Darwin - Mac, Win32 - Windows, Linux).
   - Ensure paths match locations of applications/ilp/pipelines/text files.

### Running the Workflow

1. Open terminal, navigate to Italiano_MK_Analysis folder.
2. Run: `pipenv shell`

Then choose:

- Via Terminal:
  Run: `python mk "your_image_folder_path"`

- Via Jupyter Notebook:
  1. Run: `jupyter notebook`
  2. Open 'MK' notebook in the jupyter folder.
  3. Set `FOLDER = "your_image_folder_path"`
  4. Run entire notebook or progress step-by-step with Shift + Enter.

## Workflow Overview

### I. MK

1. Unpack tif stacks into *single_images* folder (convert to 8-bit).
2. Process images with ilastik:
   - Create *ilastik* folder
   - Generate h5 files and probability maps
3. Create 'mk.txt' and copy machine learning rules file.
4. Run CellProfiler:
   - Generate results in *output* folder
   - Create overlay, mk_labels, and pplt_labels folders
5. Format and create Excel files with various metrics.
6. Generate graphs for key metrics.
7. Move raw result files to 'raw_files' folder.

### II. Skel

1. Create 'skeleton' folder.
2. Generate 'skel.txt' with file paths.
3. Run CellProfiler:
   - Create overlay and branchpoints folders
4. Generate Excel results for various skeletal metrics.

### III. Fluo

1. Unpack fluorescent stacks in 'fluo/fluo_single' folder.
2. Create 'fluo.txt' with file paths.
3. Run CellProfiler:
   - Generate overlay folder
4. Create Excel results for fluorescence metrics.
