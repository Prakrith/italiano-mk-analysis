# Workflow Overview

This automated image processing workflow analyzes phase-contrast, tif time-lapses of Megakaryocytes & Pro-platelet differentiation using ilastik & CellProfiler.

## I. MK

1. Unpack tif stacks into *single_images* folder (convert to 8-bit).
2. Process images with ilastik:
   - Create *ilastik* folder
   - Generate h5 files and probability maps
3. Create `mk.txt` and copy machine learning rules file.
4. Run CellProfiler:
   - Generate results in *output* folder
   - Create overlay, mk_labels, and pplt_labels folders
5. Format and create Excel files with various metrics.
6. Generate graphs for key metrics.
7. Move raw result files to `raw_files` folder.

## II. Skel

1. Create `skeleton` folder.
2. Generate `skel.txt` with file paths.
3. Run CellProfiler:
   - Create overlay and branchpoints folders
4. Generate Excel results for various skeletal metrics.

## III. Fluo

1. Unpack fluorescent stacks in `fluo/fluo_single` folder.
2. Create `fluo.txt` with file paths.
3. Run CellProfiler:
   - Generate overlay folder
4. Create Excel results for fluorescence metrics.