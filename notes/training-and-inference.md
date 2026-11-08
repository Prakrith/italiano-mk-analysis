# Training and inference in the legacy pipeline (Phase 1 notes)

Scope: how the supervised segmentation step is trained (from `ilps/mouse.ilp` and `ilps/human.ilp`) and how inference runs (from `mk/util/il.py`). Not covered: retraining, running inference, CellProfiler stages, method selection, `ilps/template.ilp` (not inspected).

Conventions. **Observed** = read from a file in this repository, with the path or line cited. **Unknown** = the files do not show it; nothing is filled in from ilastik defaults or memory. **Consistent with** = arithmetic or naming agrees but no stored field states it. HDF5 paths are relative to the file root.

## 1. How the files were inspected

- Static, read-only inspection with Python `h5py` 3.14.0 and `numpy` 2.0.2 in a throwaway virtualenv outside the repository. No ilastik, CellProfiler or legacy Python was run (open item U-2 is therefore not needed for this task). `h5py.File(path, "r")` only; the contents of the `ClassifierFactory` pickle were read as raw bytes and not unpickled.
- Reproduce the core HDF5-derived values below (hashes, feature selections, label names and order, per-image and per-class annotation counts, forest options, factory bytes, image references with embedded dataset shapes and dtypes, export settings, mouse-versus-human equality) with `python3 -I notes/inspect_ilp.py ilps/mouse.ilp ilps/human.ilp` (needs `h5py` and `numpy`; read-only). It prints only the first and last feature names, and does not print `blockSlice` geometry, axis tags, role names, root attributes or feature-selection storage versions; those were read during inspection and are not covered by the script. Its output for both files matched the numbers in this file when last run.
- SHA-256 of the files at inspection (the script prints them; the same values were observed before and after inspection):
  - `ilps/mouse.ilp` `44e7d09e6d3738eb1d207e9a692704f760a6abe91f2002a10cf75a7c9b7734e5` (20,720,555 bytes)
  - `ilps/human.ilp` `f8e4f7aa3551686c7d71082de980845792549b210313ba1368093ea99a8dcdfd` (85,908,711 bytes)
- Both files: `file` reports HDF5 version 5 data; root attributes: none.

| Root dataset | mouse.ilp | human.ilp |
|---|---|---|
| `/workflowName` | `AutocontextTwoStage` | `AutocontextTwoStage` |
| `/ilastikVersion` | `1.3.2rc2` | `1.3.2rc2` |
| `/time` (last save) | Fri May 10 11:10:47 2019 | Thu Mar 21 06:32:06 2019 |
| `/currentApplet` | 4 | 4 |

Top-level groups in both: `FeatureSelections`, `FeatureSelections01`, `Input Data`, `PixelClassification`, `PixelClassification01`, `Prediction Export`.

## 2. Stage structure

Observed: `/workflowName` is `AutocontextTwoStage`. Stage 1 lives in `FeatureSelections` + `PixelClassification`; stage 2 in `FeatureSelections01` + `PixelClassification01` (the `01` suffix is the second stage; the suffix-to-stage mapping is read from the group names and the label sets below, not from a stored field).

| | Stage 1 (`PixelClassification`) | Stage 2 (`PixelClassification01`) |
|---|---|---|
| Label names (`LabelNames`) | `background`, `background_cell`, `white`, `black`, `gray` (5) | `background`, `cell_boundary`, `mk`, `pplt` (4) |
| Classifier input columns (`ClassifierForests/feature_names`, `Forest0000/_ext_param/column_count_`) | 49 | 294 |

- Stage-2 input columns: 294 = 49 x 6. Observed in `PixelClassification01/ClassifierForests/feature_names`: every one-output feature name appears with channel suffixes `[0]`..`[5]` and every two-output feature name with `[0]`..`[11]`, i.e. the same 37 selected filter-scale pairs (49 feature columns per input channel) are applied to 6 input channels. The stored column order is filter, then scale, then channel, not six blocks of 49. **Consistent with** Autocontext stage 2 seeing the raw image plus the 5 stage-1 probability channels (1 + 5 = 6); no stored field states the stage-2 input composition, so it is not verified further.
- The meaning of the stage-1 label names `white`, `black`, `gray` and `background_cell` is **unknown** from the files (names only; no description stored). They are not exported by `il.py` (section 6).
- Stage 1 and stage 2 have identical feature selections (section 3) and identical classifier settings except for the values in section 5.

## 3. Stored feature selections and scales

Observed at `FeatureSelections/` (stage 1) and `FeatureSelections01/` (stage 2); the datasets `FeatureIds`, `Scales`, `SelectionMatrix`, `ComputeIn2d` are element-wise identical across stages **and** across mouse.ilp and human.ilp (checked programmatically). `StorageVersion` = `0.1`.

- `Scales` = 0.3, 0.7, 1.0, 1.6, 3.5, 5.0, 10.0. `ComputeIn2d` = true for all 7 scales.
- `SelectionMatrix` (rows `FeatureIds`, columns `Scales`), 1 = selected:

| Feature (`FeatureIds`) | 0.3 | 0.7 | 1.0 | 1.6 | 3.5 | 5.0 | 10.0 |
|---|---|---|---|---|---|---|---|
| GaussianSmoothing | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| LaplacianOfGaussian | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| GaussianGradientMagnitude | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| DifferenceOfGaussians | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| StructureTensorEigenvalues | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| HessianOfGaussianEigenvalues | 0 | 1 | 1 | 1 | 1 | 1 | 1 |

- 37 selected feature-scale pairs. Expanded to 49 columns per input channel because the two eigenvalue features output 2 values each (7 + 6 + 6 + 6 + 12 + 12 = 49; column names in `ClassifierForests/feature_names`, e.g. `Gaussian Smoothing (σ=0.3) in 2D`, `Hessian of Gaussian Eigenvalues (σ=10.0) in 2D [1]`). Stage 1 has 49 columns (single raw channel); stage 2 has 294 (section 2).

## 4. Label names and order; reconciliation with `LABEL_LIST`

Observed in both files:

- `PixelClassification01/LabelNames` = [`background`, `cell_boundary`, `mk`, `pplt`]; `PixelClassification01/ClassifierForests/known_labels` = [1, 2, 3, 4]; `Forest0000/_ext_param/labels` = [1, 2, 3, 4].
- `mk/util/il.py:16`: `LABEL_LIST = ["background", "cell_boundary", "mk", "pplt"]`, with the comment at line 15 saying it corresponds to the stage-2 export order.
- Reconciled: the stored stage-2 label order equals `LABEL_LIST` element for element, in both files. `il.py:55` names output channel `i` as `LABEL_LIST[i]`, and `mk/__main__.py:17` (`PRBSTG_DICT`) expects the matching four file suffixes.
- **Resolved from source, not run (`notes/ilastik-internals.md` section 12):** that exported channel `i` of the `probabilities stage 2` array is label `i+1`. The files store the label order but not the export channel order; this is how ilastik behaves, not a stored fact. Confirming by running was not done.
- Label colors (`LabelColors`, `PmapColors`) and `LabelNames` are identical between mouse.ilp and human.ilp.

## 5. Classifier type and recoverable settings

Observed in both stages of both files:

- `ClassifierForests/pickled_type` = `lazyflow.classifiers.parallelVigraRfLazyflowClassifier.ParallelVigraRfLazyflowClassifier`: a random forest (VIGRA implementation, via ilastik's lazyflow). The classifier is a set of forests, each in `ClassifierForests/Forest0000`, `Forest0001`, ... with `Tree_<n>/topology` and `Tree_<n>/parameters` datasets (the stored trees).
- `ClassifierFactory` (a pickle, read as raw bytes) states: `_num_trees` = 100, `_num_forests` = 4, `VERSION` = 2, `_label_proportion` = None, `_variable_importance_enabled` = 0 (`I00`), `_kwargs` = empty dict. Identical in all four stored factories.
- Per forest `_options` (identical in all forests, both stages, both files except `tree_count_`): `min_split_node_size_` = 1, `mtry_` = 0, `mtry_switch_` = 6, `mtry_func_` = 0, `sample_with_replacement_` = 1, `stratification_method_` = 3, `training_set_proportion_` = 1.0, `training_set_size_` = 0, `training_set_calc_switch_` = 1, `predict_weighted_` = 0, `prepare_online_learning_` = 0. The numeric codes (`mtry_switch_`, `stratification_method_`, ...) are raw VIGRA enum values; their meanings were decoded from the VIGRA source (`notes/ilastik-internals.md` section 7).
- Per forest `_ext_param`: `class_weights_` all 1.0; `problem_type_` = 1; `used_` = 1. `actual_mtry_` records the features tried per split: 7 (stage 1, 49 columns) and 17 (stage 2, 294 columns). **Consistent with** the square root of the column count; the selection rule itself is not stored as a readable setting.
- Training rows: `Forest0000/_ext_param/row_count_` equals the labeled-pixel totals in section 7 in every case (cross-check passed): mouse 172 / 285, human 236 / 951 (stage 1 / stage 2). This is consistent with each labeled pixel being one training example (`actual_msample_` also equals `row_count_`); which rows were used is not independently verified.

| | mouse.ilp | human.ilp |
|---|---|---|
| Forests stored in `ClassifierForests` | 8 (`Forest0000`..`Forest0007`) | 4 (`Forest0000`..`Forest0003`) |
| Trees per forest (`_options/tree_count_`) | 13,13,13,13,12,12,12,12 (sum 100) | 25 each (sum 100) |
| `_num_forests` in factory pickle | 4 | 4 |

- The mouse file stores 8 forests although its factory pickle says 4. The reason is **unknown** (not inferred); the total of 100 trees agrees with `_num_trees` in all cases.
- Hyperparameters not stored in the file (for example the maximum tree depth, class balancing beyond `class_weights_`, the random seed) are **unknown**.

## 6. Inference (`mk/util/il.py` and its caller)

Observed, with line numbers (static reading only; nothing was run):

- Settings: `il.py:12-13` read `ilastik_app` and `ilp` from `config.ini` through `tools.read_config` (`mk/util/tools.py:24-36`, which selects the section by `sys.platform`). In `config.ini` the `ilp` key points at `mouse.ilp` for all three platform sections (lines 3, 19, 35), and the repository code does not reference `human.ilp` (grep found no use). Owner statement (not verified from the files): both `.ilp` files are interchangeable projects for running inference on images. `human.ilp` was created for images of human megakaryocytes and `mouse.ilp` for mouse ones (the owner is not sure the species split was needed); `mouse.ilp` was used more. Because `il.py:13` reads a single `ilp` path from `config.ini`, using `human.ilp` means changing that setting; nothing in the code selects a project by species.
- Entry flow in `mk/__main__.py`: `stack.unpack(single.path, 8)` (line 33); `Ilastik(...)` and `ilastik.check(PRBSTG_DICT, single.df)` (37-39) build the list of images to process (`mk/util/folder.py:161-195`). Observed behavior: if the `ilastik` folder holds exactly 4 x as many PNGs as there are single images, nothing is run, but only when the `is` comparison on line 168 succeeds (it compares integers by identity rather than `==`, which can fail for equal larger values, in which case execution falls through to the filename check; it checks no filenames itself); if it is empty, all images are run; otherwise `check_incomplete` (lines 180-195) treats an image as already processed as soon as **any one** of its four probability PNGs exists, so an image with only some of its maps would be skipped (limitation read from the code, not run); `RunIL(ilastik.incomplete)` (line 40) runs ilastik on those images only.
- `RunIL.run` (`il.py:23-31`): applies `process` to each row; in a notebook with a progress bar, otherwise a plain `apply`, where an `OSError` ends the program with `>>> Check ilastik path and config.ini.` (lines 28-31).
- `RunIL.process` (`il.py:33-58`) per image:
  1. Builds `<name>_Probabilities Stage 2.h5` (lines 36-37).
  2. Starts ilastik with `subprocess.Popen([ILASTIK_PATH, "--headless", "--export_source=probabilities stage 2", "--output_format=hdf5", "--project=<ILP>", <image path>], stdout=PIPE)` (lines 40-46) and waits with `communicate()` (line 47). The return code is not checked and stderr is not captured (it passes through to the console). A failed ilastik run therefore does not stop the code at this point; what happens next depends on what is on disk (a missing export file raises an `OSError` at line 50, while a stale or partial export file would be read without any check).
  3. Opens the HDF5 file and reads dataset `exported_data` with `.value` (lines 50-51). `.value` was removed in h5py 3, so this code needs an old h5py (relevant to U-2). The `.ilp` agrees on the dataset name: `Prediction Export/OutputInternalPath` = `exported_data`, `OutputFormat` = `hdf5`, `OutputFilenameFormat` = `{dataset_dir}/{nickname}_{result_type}` (identical in both files).
  4. For each index `i` along axis 2 (line 53) takes the 2-D slice `[:, :, i]`, converts it with `skimage.img_as_uint` (line 54) and writes `<name>_<LABEL_LIST[i]>_prbstg2_<i>.png` into `<image folder>/../ilastik/` (lines 55-56). The `ilastik` folder is not created in `il.py`; the caller creates it with `stack.folder('ilastik')` (`mk/__main__.py:37`, `mk/util/folder.py:17-18`).
  5. Deletes the HDF5 file (line 58).
- Output dtype and range: `img_as_uint` converts a float image in [0, 1] to 16-bit (0-65535). That the exported probabilities are floats in [0, 1] is an assumption of the code; the `.ilp` stores no export dtype or normalisation setting (`Prediction Export` has only `OutputFilenameFormat`, `OutputFormat`, `OutputInternalPath` and `StorageVersion` = `0.1`). The axis order of `exported_data` (that axis 2 is the class channel) is likewise assumed by line 53 and not verifiable from the project file. Both are resolved from the ilastik source, not run: `notes/ilastik-internals.md` section 12.
- What is **not** stored in the `.ilp`: the export source (`probabilities stage 2` is given only on the command line, `il.py:42`), so the `.ilp` alone does not say what is exported.
- 8-bit input assumption: the training images stored in the `.ilp` are all `uint8` (section 7). `docs/Setup.md:6` tells the user to convert training images to 8-bit and `docs/Prerequisites.md:6` requires 8-bit single images. In code, `stack.unpack(..., 8)` (`mk/__main__.py:33`) converts to 8-bit only in the 4-D (color) branch (`mk/util/folder.py:101-112`, `img_as_ubyte` at line 110); the branch for ordinary stacks (113-117) writes the slices unchanged, so 8-bit input is then a precondition, not something `il.py` checks. `il.py` itself has no check of the input bit depth.
- Hand-off: the four probability PNGs per image (`background`, `cell_boundary`, `mk`, `pplt`) are appended to the CellProfiler image list (`mk/__main__.py:45`, `single.list + ilastik.list`). Downstream handling is out of scope here; an outline is in `notes/cellprofiler-and-rules.md`.
- Version note: `config.ini` line 13 names ilastik 1.3.3post2 (macOS) while both `.ilp` files were last saved by 1.3.2rc2 (`/ilastikVersion`). Whether the newer app loads them without change is **unknown**.

## 7. Training annotations

Definitions. "Annotation count" = number of labeled pixels per class in the `LabelSets` blocks (nonzero values; `0` = unlabeled). Per image (one `labelsNNN` set per input lane) and per stage. Each block is a rectangular patch (`blockSlice` attribute, y then x) holding label values.

Paths: `PixelClassification/LabelSets/labels<NNN>/block<NNNN>` (stage 1) and `PixelClassification01/LabelSets/labels<NNN>/block<NNNN>` (stage 2); `labels<NNN>` is the lane with the same index in `Input Data/infos/lane<NNNN>`. The stage totals equal `row_count_` of the trained forests (section 5).

### Counts


#### mouse, stage 1 (`PixelClassification/LabelSets`)

| label set | image nickname | blocks | background | background_cell | white | black | gray | total |
|---|---|---|---|---|---|---|---|---|
| `labels000` | untreated1 | 4 | 3 | 3 | 3 | 3 | 3 | 15 |
| `labels001` | drug | 3 | 4 | 3 | 3 | 3 | 3 | 16 |
| `labels002` | drug2 | 5 | 3 | 3 | 3 | 3 | 3 | 15 |
| `labels003` | pbs | 2 | 3 | 3 | 3 | 3 | 3 | 15 |
| `labels004` | puro | 6 | 7 | 7 | 7 | 7 | 7 | 35 |
| `labels005` | untreated2 | 5 | 3 | 3 | 4 | 4 | 4 | 18 |
| `labels006` | dmso | 3 | 3 | 3 | 3 | 3 | 3 | 15 |
| `labels007` | drug3 | 3 | 4 | 4 | 4 | 4 | 4 | 20 |
| `labels008` | 190430_SLF1_A1_1-0012 | 3 | 3 | 4 | 5 | 3 | 8 | 23 |
| **all** | | 34 | 33 | 33 | 35 | 33 | 38 | 172 |


#### mouse, stage 2 (`PixelClassification01/LabelSets`)

| label set | image nickname | blocks | background | cell_boundary | mk | pplt | total |
|---|---|---|---|---|---|---|---|
| `labels000` | untreated1 | 4 | 8 | 8 | 8 | 8 | 32 |
| `labels001` | drug | 2 | 4 | 4 | 4 | 4 | 16 |
| `labels002` | drug2 | 2 | 4 | 0 | 4 | 4 | 12 |
| `labels003` | pbs | 2 | 6 | 8 | 8 | 8 | 30 |
| `labels004` | puro | 5 | 8 | 5 | 5 | 4 | 22 |
| `labels005` | untreated2 | 7 | 14 | 10 | 22 | 4 | 50 |
| `labels006` | dmso | 6 | 25 | 2 | 0 | 14 | 41 |
| `labels007` | drug3 | 2 | 2 | 8 | 11 | 3 | 24 |
| `labels008` | 190430_SLF1_A1_1-0012 | 5 | 10 | 10 | 30 | 8 | 58 |
| **all** | | 35 | 81 | 55 | 92 | 57 | 285 |


#### human, stage 1 (`PixelClassification/LabelSets`)

| label set | image nickname | blocks | background | background_cell | white | black | gray | total |
|---|---|---|---|---|---|---|---|---|
| `labels000` | 190311_PV_20X_C4_1-0021 | 4 | 4 | 4 | 4 | 4 | 4 | 20 |
| `labels001` | 190311_PV_20X_C4_2-0011 | 4 | 4 | 4 | 4 | 4 | 4 | 20 |
| `labels002` | 190311_PV_20X_C4_3-0005 | 5 | 3 | 3 | 3 | 3 | 3 | 15 |
| `labels003` | 190311_PV_20X_C4_4-0000 | 6 | 4 | 5 | 4 | 4 | 4 | 21 |
| `labels004` | 190311_PV_20X_C4_4-0008 | 3 | 5 | 5 | 5 | 5 | 5 | 25 |
| `labels005` | 190311_PV_20X_E8_1-0009 | 6 | 5 | 5 | 5 | 5 | 5 | 25 |
| `labels006` | 190311_PV_20X_E8_2-0016 | 5 | 5 | 5 | 5 | 5 | 5 | 25 |
| `labels007` | 190311_PV_20X_E8_3-0023 | 4 | 6 | 6 | 6 | 6 | 6 | 30 |
| `labels008` | 190311_PV_20X_E8_4-0008 | 5 | 4 | 5 | 4 | 4 | 4 | 21 |
| `labels009` | 190311_PV_20X_C4_2-0005 | 3 | 5 | 5 | 5 | 4 | 5 | 24 |
| `labels010` | 190311_PV_20X_E8_4-0024 | 2 | 2 | 2 | 2 | 2 | 2 | 10 |
| **all** | | 47 | 47 | 49 | 47 | 46 | 47 | 236 |


#### human, stage 2 (`PixelClassification01/LabelSets`)

| label set | image nickname | blocks | background | cell_boundary | mk | pplt | total |
|---|---|---|---|---|---|---|---|
| `labels000` | 190311_PV_20X_C4_1-0021 | 1 | 6 | 6 | 17 | 0 | 29 |
| `labels001` | 190311_PV_20X_C4_2-0011 | 4 | 105 | 19 | 44 | 59 | 227 |
| `labels002` | 190311_PV_20X_C4_3-0005 | 7 | 44 | 13 | 44 | 20 | 121 |
| `labels003` | 190311_PV_20X_C4_4-0000 | 4 | 11 | 12 | 0 | 22 | 45 |
| `labels004` | 190311_PV_20X_C4_4-0008 | 4 | 3 | 0 | 44 | 20 | 67 |
| `labels005` | 190311_PV_20X_E8_1-0009 | 1 | 18 | 4 | 76 | 0 | 98 |
| `labels006` | 190311_PV_20X_E8_2-0016 | 4 | 23 | 12 | 58 | 0 | 93 |
| `labels007` | 190311_PV_20X_E8_3-0023 | 4 | 13 | 22 | 85 | 0 | 120 |
| `labels008` | 190311_PV_20X_E8_4-0008 | 2 | 0 | 0 | 42 | 0 | 42 |
| `labels009` | 190311_PV_20X_C4_2-0005 | 1 | 5 | 5 | 29 | 28 | 67 |
| `labels010` | 190311_PV_20X_E8_4-0024 | 5 | 3 | 0 | 39 | 0 | 42 |
| **all** | | 37 | 231 | 93 | 478 | 149 | 951 |

Observations: the numbers of labeled pixels are small (172 to 951 per file and stage). Class balance is uneven in stage 2 (for example mouse `dmso` has 25 `background`, 2 `cell_boundary`, 0 `mk` and 14 `pplt` pixels; human has several images with 0 `pplt` pixels). Whether these counts are all the annotations that were ever drawn, or only those saved in the final project state, is **unknown**.

### Image references stored in the file, separate from images available

Observed per lane at `Input Data/infos/lane<NNNN>/Raw Data/`: `nickname`, `filePath` (a relative path ending in the TIF file name), `location` = `ProjectInternal`, `shape` = (1040, 1408), `dtype` = `uint8`, `axistags` = y, x, `datasetId`. `Role Names` = `Raw Data`, `Prediction Mask`; the `Prediction Mask` group is empty in every lane (no mask is stored; whether one was used is not shown).

- Referenced images: mouse.ilp has 9 (nicknames `untreated1`, `drug`, `drug2`, `pbs`, `puro`, `untreated2`, `dmso`, `drug3`, `190430_SLF1_A1_1-0012`); human.ilp has 11 (`190311_PV_20X_C4_1-0021`, `..._C4_2-0011`, `..._C4_3-0005`, `..._C4_4-0000`, `..._C4_4-0008`, `..._E8_1-0009`, `..._E8_2-0016`, `..._E8_3-0023`, `..._E8_4-0008`, `..._C4_2-0005`, `..._E8_4-0024`; all prefixed `190311_PV_20X_`).
- Available: the original TIF files are **not available** here. The stored `filePath` values are relative paths that point outside the repository (to a folder on the original author's machine), they do not exist relative to this repository, and the repository contains no `.tif`, `.png` or `.h5` files.
- Available inside the project: `location` = `ProjectInternal` and every lane's `datasetId` has a matching dataset under `Input Data/local_data/<datasetId>` (shape (1040, 1408), `uint8`): 9 in mouse.ilp, 11 in human.ilp. In the two inspected files these embedded copies are the only training images stored (`ilps/template.ilp` was not inspected); this is consistent with `docs/Setup.md:9`, "Copied to Project File"). They were not extracted or compared with originals here. Whether they are identical to the original TIFs is **unknown**. Where the original images exist is **unknown** (U-1a stays open).
- Independent evaluation ground truth: none found in the repository or the `.ilp` files (U-1b, accepted as a limitation on the owner's statement that none exists). The labels above are training annotations, not an evaluation set; the project file stores no held-out data or accuracy measure.

## 8. mouse.ilp versus human.ilp

| Topic | Same in both | Different |
|---|---|---|
| Workflow, ilastik version | `AutocontextTwoStage`, `1.3.2rc2` | last saved 2019-05-10 (mouse) vs 2019-03-21 (human) |
| Features and scales (both stages) | identical selection, scales, 2-D flag | none |
| Label names, order, colors (both stages) | identical (stage 2 equals `LABEL_LIST`) | none |
| Prediction export settings | identical | none |
| Classifier family and `_options` | VIGRA random forest, 100 trees in total, same options | mouse: 8 forests of 13/12 trees; human: 4 forests of 25 trees |
| Training images | all `uint8`, 1040 x 1408, embedded in the file | mouse: 9 images (cell-treatment names plus one `190430_SLF1` image); human: 11 images (`190311_PV_20X_*`) |
| Labeled pixels, stage 1 | five classes in both | mouse 172, human 236 |
| Labeled pixels, stage 2 | four classes in both | mouse 285 (81/55/92/57), human 951 (231/93/478/149) in the order background/cell_boundary/mk/pplt |
| File size | | mouse 20.7 MB, human 85.9 MB |
| Used by code | | `config.ini` points to `mouse.ilp` only; `human.ilp` is not referenced |

## 9. Open points

Status after the source study (`notes/ilastik-internals.md`, section 14 there has the detail). "From source" means read in ilastik 1.3.2rc2 source and not confirmed by running it.

- Exported channel order and dtype of `probabilities stage 2`: **resolved from source**: `(y, x, class)`, `float32`, nominal range 0 to 1, class index = label - 1; `il.py` passes no ilastik export-normalization options and `mouse.ilp` stores none, so ilastik writes unscaled floats (the later PNG conversion with `skimage.img_as_uint` at `il.py:54` is a separate step).
- Why mouse.ilp stores 8 forests while the factory records 4: forest counts match the default worker-cap arithmetic (8 = cap; 4 would match a 4-worker pool, a possible explanation only) and option codes decoded; why the saved pickle says 4 for mouse is still **unknown**.
- Meaning of stage-1 label names `white`, `black`, `gray`, `background_cell`: the code uses only the class index. Owner statement (2026-11-06, not checkable in the files): they are empirical descriptions of what was seen in the image while labeling; stage 1 was labeled with single-pixel seeds to define boundaries precisely and limit class bleeding, and stage 2 with dense regional brush strokes to give morphological context and spatial continuity. Observation from `mouse.ilp` (read-only): stored label blocks hold a median of 5 labeled pixels per block in stage 1 (172 pixels, 34 blocks, max 18) and 8 in stage 2 (285 pixels, 35 blocks, max 24). Stage 2 has more labeled pixels, but nothing in the file shows dense regional strokes; block geometry is storage, not brush shape, so the stroke style stays the owner's account only.
- Whether the embedded images match the original TIFs; where originals and any independent ground truth are (U-1a, U-1b): owner statement 2026-11-07 that they do not exist, so this cannot be checked; accepted as a limitation.
- Whether ilastik 1.3.3post2 (config) loads these 1.3.2rc2 projects unchanged: not run. For the Autocontext stage-2 input and 8-bit images the code compared is equivalent in both versions; loading of the whole project was not compared.
- Independent review of the source notes: a Codex review was run (see U-4 and VER-3 in `PROJECT.md`); not reviewed by the owner.
