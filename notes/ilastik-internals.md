# ilastik internals: features, random forest, Autocontext and export (from source)

Tasks `ums` (sections 1 to 8) and `y23` (sections 9 to 14). Companion to `training-and-inference.md`. Scope: how ilastik pixel classification computes features, builds training rows, trains and applies the random forest (`ums`); how the two Autocontext stages are wired, what the headless `probabilities stage 2` export writes, and whether a headless run changes the project (`y23`).

Conventions. **Source fact** = read in the cited file and line. **Derived** = arithmetic on source facts, not run. **Hypothesis** = plausible, not shown by what was read. **Unknown** = not found. Third-party code is cited, not copied; short phrases are quoted.

## 1. Versions read

The `.ilp` files were saved by ilastik 1.3.2rc2 (`/ilastikVersion`); `config.ini` names 1.3.3post2 (macOS) and 1.3.2post1 (Windows). Source was read from clones in a scratch directory (not in this repository):

| Repository | Tag / commit read |
|---|---|
| `ilastik/ilastik-meta` tag `1.3.2rc2` | `f640436`; submodules `ilastik` `32b7a41`, `lazyflow` `f1eaa47`, `volumina` `fd9c2bf` |
| `ilastik/ilastik-meta` tag `1.3.3post2` | `be4bdc2`; submodules `ilastik` `318782a`, `lazyflow` `d266869`, `volumina` `e66ca67` |
| `ukoethe/vigra` tag `Version-1-11-1` | `ed1e79e` |

- Line numbers below are for tag `1.3.2rc2` (the version that saved the files) unless stated. For the constructs cited in sections 3 to 5, `1.3.3post2` has the same logic (same line content apart from code formatting); only these were compared, not the whole files.
- **Unknown (U-5):** which VIGRA version, and whether the `fastfilters` library, was inside the ilastik binary actually used. Both are conda-installed binary dependencies, not part of `ilastik-meta`. `Version-1-11-1` was read as a stand-in; VIGRA statements are therefore **Source fact for that tag, unconfirmed for the bundled build**.

## 2. Pipeline in one picture

raw 2-D image -> per-pixel features (section 3) -> feature vector per pixel. Training: vectors at labeled pixels only (section 4) -> random forest (section 5). Inference: vectors at every pixel -> forest -> per-class value per pixel (section 6).

## 3. Features

Where: `lazyflow/lazyflow/operators/opPixelFeaturesPresmoothed.py` (the feature-selection applet uses it: `ilastik/ilastik/applets/featureSelection/opFeatureSelection.py:100`), with the filters in `lazyflow/lazyflow/operators/filterOperators.py`.

**Source facts**
- Names: the strings in `.ilp` `feature_names` (for example `Gaussian Smoothing (σ=0.3) in 2D`) are built at `opPixelFeaturesPresmoothed.py:144-171`; two-output filters get a ` [k]` suffix (same area). This matches the `.ilp`, which is evidence the tag matches the files' writer.
- **Presmoothing.** For each selected scale `s` the whole input is first Gaussian-smoothed, then each filter runs on the smoothed copy (`opPixelFeaturesPresmoothed.py:389-399`). The presmoothing sigma is `sqrt(s^2 - 1)` if `s > 1`, else `s` (lines 390-392). The filter itself runs with sigma `min(s, 1)` (`self.newScales`, lines 128-132).
- Filter parameters (`opPixelFeaturesPresmoothed.py`, sigma = that `newScales` value, call it `s'`):
  - Gaussian smoothing: sigma `s'` (`OpGaussianSmoothing`).
  - Laplacian of Gaussian and Hessian of Gaussian eigenvalues and Gaussian gradient magnitude: scale/sigma `s'`.
  - Structure tensor eigenvalues: inner scale `s'`, outer scale `0.5 * s'` (lines 150-152).
  - Difference of Gaussians: `Gaussian(s') - Gaussian(0.66 * s')` (lines 162-164; subtraction at `filterOperators.py:396-397`).
- Kernel half-widths: the presmoothing uses `window_size` 3.5 (`WINDOW_SIZE`, `opPixelFeaturesPresmoothed.py:66`, used at lines 475-489); the filters use `window_size_feature = 2` (`filterOperators.py:56`, applied at line 104).
- 2-D mode: with "in 2D" the smoothing sigma is `(0, sigma, sigma)` (`opPixelFeaturesPresmoothed.py:485`), i.e. no smoothing across z. Both `.ilp` files have 2-D set for every scale, so this is the used path.
- Implementation switch: if the `fastfilters` library imports, it is used instead of VIGRA's filters (`filterOperators.py:35-39`; for example `fastfilters.gaussianSmoothing` at line 372, VIGRA's at 375).
- Input is converted to float32 before filtering (`opPixelFeaturesPresmoothed.py:359-366`, cast at line 360); the image is not rescaled or normalized in this operator.

**Derived (arithmetic, not run)**
- For the single-Gaussian filters (Gaussian smoothing, Laplacian of Gaussian, gradient magnitude, Hessian eigenvalues), treating Gaussians as ideal (finite, discretized kernels ignored), Gaussian smoothings add variances. Difference of Gaussians (second sigma 0.66 of the first) and the structure tensor (outer scale 0.5 of the inner) use more than one scale and do not reduce to one effective sigma (`opPixelFeaturesPresmoothed.py:150-164`). For `s > 1` the total smoothing before the filter's own kernel is `sqrt((s^2 - 1) + 1^2) = s`, so the nominal scale is the effective scale. For `s <= 1` (this project uses 0.3, 0.7, 1.0) the image is smoothed with sigma `s` and then the filter runs with sigma `s`, giving a total of `sqrt(2) * s` (about 0.42 for the nominal 0.3). So nominal scales at or below 1 are not the effective ones. This is read from the code and not measured on an image.

**Unknown**
- Order of the two eigenvalue outputs (largest first or not): VIGRA's eigenvalue routines were not read.
- Numerical differences between the `fastfilters` and VIGRA paths.

## 4. Training rows

- The labels are read per block; positions with a non-zero label are taken, and the feature vector at each such pixel becomes a row, with the label as the target (`lazyflow/lazyflow/operators/opFeatureMatrixCache.py:253-285`, in particular `numpy.nonzero(labels[...,0])` at line 256 and the feature extraction at line 285).
- The rows are concatenated and passed to `create_and_train` (`lazyflow/lazyflow/operators/classifierOperators.py:322`), which casts features to float32 and labels to uint32 (`classifiers/parallelVigraRfLazyflowClassifier.py:111-115`).
- So every labeled pixel is one training row, and unlabeled pixels give no rows or targets (their intensities still enter the features of nearby labeled pixels, because features are computed before the labeled positions are selected). This agrees with `row_count_` equalling the labeled-pixel totals in the `.ilp` (notes `training-and-inference.md` section 5). No feature scaling or class balancing step was found in these functions.

## 5. Training the forest

**Source facts**
- `ilastik` uses `ParallelVigraRfLazyflowClassifierFactory` ("a forest-of-forests", `parallelVigraRfLazyflowClassifier.py:53-58`, docstring at lines 53-56). It splits `num_trees_total` (100) over `num_forests` forests: each gets `100 // F` trees and the first `100 % F` forests get one extra (lines 102-106). Each forest is `vigra.learning.RandomForest(tree_count, **kwargs)` (line 134) trained independently by `learnRF` (line 169).
- `num_forests` default: "`num_forests or Request.global_thread_pool.num_workers`" (line 86), evaluated when the factory object is created. The worker-pool default is `min(multiprocessing.cpu_count(), 8)` (`lazyflow/lazyflow/request/request.py:114`).
- The default factory is created when the pixel-classification operator is defined (`ilastik/ilastik/applets/pixelClassification/opPixelClassification.py:67`, `ParallelVigraRfLazyflowClassifierFactory(100)`); the GUI's classifier chooser creates another with the same call (`pixelClassificationGui.py:115`) and sets the selected one into the operator (line 149).
- The factory is saved as a pickle with `pickle.dumps(value, 0)` (`ilastik/ilastik/applets/base/appletSerializer.py:811-814`); on load it is unpickled and put back into the slot only if its `VERSION` matches (lines 822-836).
- Only the factory's constructor arguments given by ilastik are passed to VIGRA; `kwargs` is empty in the files, so VIGRA's Python defaults apply: `min_split_node_size=1`, `training_set_size=0`, `training_set_proportions=1.0`, `sample_with_replacement=True`, and an `mtry` argument whose binding default is -1 (`vigranumpy/src/core/random_forest.cxx:359-364`); the binding's docstring gives the default as `RF_SQRT` (line 369), and the stored `mtry_switch_` below agrees. How -1 is mapped was not traced.
- Option codes. VIGRA's enum is `RF_EQUAL, RF_PROPORTIONAL, RF_EXTERNAL, RF_NONE, RF_FUNCTION, RF_LOG, RF_SQRT, RF_CONST, RF_ALL` (`include/vigra/random_forest/rf_common.hxx:140-148`), which are 0 to 8 by C++ rules. So the stored `.ilp` values mean: `stratification_method_` 3 = `RF_NONE` (no class stratification), `mtry_switch_` 6 = `RF_SQRT`, `training_set_calc_switch_` 1 = `RF_PROPORTIONAL` (with proportion 1.0 and sampling with replacement, each tree trains on a bootstrap sample as large as the training set).
- `RF_SQRT`: features per split = `floor(sqrt(n_features) + 0.5)` (`rf_common.hxx:457`). That is 7 for 49 columns and 17 for 294, matching the recorded `actual_mtry_`.
- Splits use the Gini criterion by default (`include/vigra/random_forest.hxx:155`, `rf_split.hxx:1130`). A leaf stores the class counts of the training samples that reached it, multiplied by `class_weights_` (all 1 in the files) and normalized to sum to 1 (`rf_split.hxx:167-191`).
- Out-of-bag (OOB) error is computed during training and logged (`parallelVigraRfLazyflowClassifier.py:154`), but `serialize_hdf5` does not write it (lines 366-402 write the forests, `known_labels`, `feature_names`, `pickled_type`); on loading, missing OOB is replaced by -1 values (line 438). **So the `.ilp` carries no accuracy estimate even though one was computed.**

**Hypothesis / unknown**
- The tree stopping rule and any depth limit were not read: **unknown**.
- Why the files' forest counts differ (section 7).

## 6. Prediction

**Source facts**
- Each tree returns the stored class distribution of the leaf the pixel falls into. With `predict_weighted_ = 0` (the recorded value) each tree contributes weight 1: the votes are the sum of those distributions divided by the total (`random_forest.hxx:1235-1318`: leaf weights fetched at line 1293, accumulated at 1301, normalized at 1317). So a forest output is the **mean of the trees' leaf class fractions**, not a count of hard votes.
- The lazyflow wrapper calls this per forest, multiplies each result by that forest's tree count, sums, and divides by the total tree count (`parallelVigraRfLazyflowClassifier.py:327` and `343`). So the final value is the mean over all 100 trees, independent of how the trees are split into forests.
- Rows whose feature vector contains NaN get all-zero output (`random_forest.hxx:1278`).
- The value for a class is therefore in [0, 1] and the classes sum to 1 for each pixel (when no NaN). That the *exported* file has this form is shown in section 12 below (derived from source, not run).

**Correction to earlier notes.** `supervised-ml-fundamentals.md` section 4 described the output as "the fraction of trees voting for each class" as a simplified picture. The source shows averaged leaf distributions, which is slightly different (and is what the review asked us to verify rather than assume). Calibration against reality is still **not established**; these numbers are averaged leaf class fractions from the training pixels, not tested probabilities.

## 7. The 8-versus-4 forest question

Observed in the files: `mouse.ilp` stores 8 forests (13+13+13+13+12+12+12+12 = 100 trees); `human.ilp` stores 4 forests of 25; both factory pickles say `_num_forests = 4`. `template.ilp` (read-only check; not otherwise inspected) holds the same factory settings (`_num_trees` 100, `_num_forests` 4) in both stages, saved 2019-02-23 by 1.3.2rc2, and no trained forests.

From the source:
- The tree split 13/13/13/13/12/12/12/12 is exactly what lines 102-106 give for 8 forests, and 4 x 25 is what they give for 4 forests. So mouse was trained with a factory whose `num_forests` was 8, and human with one whose value was 4.
- 8 is the cap of the default worker pool (`min(cpu_count, 8)`, `request.py:114`); 4 would match a 4-worker pool. This is a possible explanation only: `num_forests` can also be passed explicitly (line 86), so the saved forests do not establish the training machine.

Not resolved: the saved pickle says 4 for mouse, yet mouse's forests were trained with 8. The code paths that could explain it are in section 5 (factory created at import time or in the GUI, saved only when the slot says it should be, restored from the pickle on load). Which one happened was not determined: **unknown**. Hypothesis (not tested): the pickled factory in `mouse.ilp` was carried over from the template and not rewritten, while the live factory used for training was a different object created on a machine with at least 8 CPUs. The headline for the reimplementation: forest count does not change the output (section 6: the average over all 100 trees), so the 8-vs-4 difference between the two models is a training-run detail and does not affect how the models should be interpreted.

## 8. What this changes for later work

- Facts for a reimplementation: the 49 features per pixel are Gaussian-family filters with the presmoothing quirk in section 3; training uses only labeled pixels (hundreds of rows for mouse); the model is a 100-tree Gini random forest, bootstrap samples, `sqrt(n_features)` candidates per split, leaves store class fractions, outputs are averaged leaf distributions.
- Stage-2 inputs and the headless export: see sections 9 to 14.
- Open here: tree stopping rule, VIGRA eigenvalue ordering, which VIGRA/fastfilters build was bundled, the pickled-factory question.

## 9. Autocontext wiring: what stage 2 receives

Paths are under `ilastik/ilastik/` (tag `1.3.2rc2`) unless noted.

**Source facts**
- The workflow `AutocontextTwoStage` is the base class built with `n_stages=2` (`workflows/newAutocontext/newAutocontextWorkflow.py:659-664`). The base creates one feature-selection applet and one pixel-classification applet per stage (lines 104-107). Each pixel-classification applet is an ordinary `OpPixelClassification`, so every statement in sections 3 to 6 holds for each stage separately. Stage 2's `.ilp` groups are `FeatureSelections01` and `PixelClassification01` (lines 184-201).
- **Stage 1 sees only the raw image.** `opData.Image` feeds stage 1's feature and classifier operators (`opFirstFeatures.InputImage.connect(opData.Image)`, line 256).
- **Stage 2 sees the raw image plus stage 1's prediction.** A stacker joins them along the channel axis: image 0 is the raw image, image 1 is stage 1's `PredictionProbabilitiesUint8` (lines 282-289); the stacked array is the input of stage 2's feature operator and classifier. For a grayscale image that is 1 + 5 = 6 channels, so channel 0 is raw and channels 1 to 5 are stage 1's classes 1 to 5 in label order (`OpMultiArrayStacker`, `lazyflow/lazyflow/operators/generic.py:179-300`).
- **Stage-1 output is converted to 8-bit by truncation.** `PredictionProbabilitiesUint8` is `(255*a).astype(numpy.uint8)` of stage 1's float probabilities (`applets/pixelClassification/opPixelClassification.py:528-529`; it is computed from the cached-feature path, line 519). So stage 2 sees stage-1 values 0 to 255 (the raw channel is also 0 to 255), quantized to 256 levels and rounded down.
- **The workflow only accepts 8-bit input.** `checkConstraints` raises `DatasetConstraintError` for any dtype other than `uint8` (lines 245-251).
- **Features are computed per input channel.** Every filter operator produces `input_channels x outputs_per_filter` channels (`filterOperators.py:115`, loop over `input_c` at lines 248-252), with the input channel as the outer index within one filter-scale pair only (across pairs the order is filter, then scale, so the columns are not six blocks of 49, one per channel). Single-output filters give 1 per channel; the two eigenvalue filters give 2 per channel in 2-D (`resultingChannels`, `filterOperators.py:432, 471`). The feature operator lists all selected filter-by-scale pairs in the order filter (outer), scale (inner), concatenating each operator's channels (`lazyflow/.../opPixelFeaturesPresmoothed.py:134-200`).
- **This reproduces the stored feature names.** Stage 2 in `mouse.ilp` has 294 distinct names, and the single-output filters carry suffixes `[0]` to `[5]` for the six input channels (read-only check: `Gaussian Smoothing (σ=0.3) in 2D [0]` to `[5]`, then σ=0.7 `[0]` to `[5]`, and so on; the eigenvalue filters run `[0]` to `[11]`). 294 = 6 input channels x 49 per-channel features, with 49 = 25 single-output pairs + 12 two-output pairs x 2 (37 pairs).
- **The two stages' labels are independent.** The line that would copy stage-1 labels into stage 2 is commented out (line 278). Labels move between stages only through the manual "distribute labels" menu action (`distribute_labels_from_current_stage`, lines 493-583), which overwrites the destination's first `n` label names and colors with the source's (lines 513-536). The files do not say whether that action was ever used; stage 2's stored names differ from stage 1's, so at least its names were not left as copied. Stage 1 has 5 classes and stage 2 has 4; stage 2 treats stage 1's output only as 5 numeric input channels and does not use their names.
- **Class names carry no meaning in the code.** Stage-1 names such as `white`, `black`, `gray`, `background_cell` are free text from the user; the code uses only the class index. What the owner meant by them is an owner statement, recorded in the training notes (section 9), not something the source shows.

**Derived (arithmetic, not run)**
- At prediction time the stage-1 class-`k` probability at pixel `p` reaches stage 2 as `floor(255 * mean_of_stage1_leaf_fractions_k(p))`, a number in 0..255.
- Because stage 2's features include Gaussian-family filters of those probability channels at scales up to 10, stage 2 can see how confident stage 1 is over a neighborhood of roughly 10 pixels, not only at the pixel itself. This is the mechanism that "Autocontext" refers to.

**Hypothesis (not shown by source)**
- When stage 2 is trained, its labeled pixels get their stage-1 inputs from the stage-1 classifier as it is at that moment. If those pixels were also labeled or used in training stage 1, stage 1's probabilities there are fit to the training pixels and are probably more confident than on new images, so stage 2 may learn to trust stage 1 more than it should. Whether that matters for these files is **unknown**.

## 10. Version difference found: how stage 1 is converted for stage 2

Between the two tags the Autocontext workflow changed what it feeds stage 2: `1.3.3post2` connects `PredictionProbabilitiesAutocontext` (`workflows/newAutocontext/newAutocontextWorkflow.py:302`) instead of `PredictionProbabilitiesUint8`, converted by `DtypeConvertFunction(input_dtype)` where `input_dtype` is the raw image's dtype (`applets/pixelClassification/opPixelClassification.py:577-579, 618-620`, `ilastik/utility/slottools.py:47-55`), and the uint8-only constraint is commented out (`newAutocontextWorkflow.py:258-265`).
- For 8-bit input (the case for these projects: the stored images are 8-bit) the integer branch gives `((255-0)*x - 0).astype(uint8)`, the same truncating conversion as `1.3.2rc2` (`slottools.py:47-52`). So, **read from the code, the stage-2 input is the same for 8-bit images in both versions.**
- For 16-bit input the two versions differ (1.3.2rc2 refuses the image; 1.3.3post2 scales to the integer type's range). For float input, 1.3.2rc2 also refuses it, while 1.3.3post2 only casts (`slottools.py:53-55`). Not relevant to the inspected projects.
- All 15 files compared between the tags differ in text (mostly code formatting); only the constructs listed in this note were read in both.

## 11. The headless call, step by step

`il.py:40-46` runs `ilastik --headless --export_source=probabilities stage 2 --output_format=hdf5 --project=<ILP> <image>` (passed as list items, so `probabilities stage 2` is one argument).

**Source facts**
1. **Project open.** `--project` is opened by `HeadlessShell.openProjectFile` (`shell/headless/headlessShell.py:81-117`). The HDF5 file is opened in mode `'r+'` unless `--readonly` is given (`shell/projectManager.py:120-143`, `ilastik_main.py:22, 373`); `il.py` does not pass `--readonly`. The workflow is chosen from the file's stored workflow name.
2. **Arguments.** The workflow first takes its own `--retrain` flag (`newAutocontextWorkflow.py:83, 89-90`). It then passes what is left to the export applet's parser (`--export_source`, `--output_format`, and others) and passes what that leaves to the batch-processing parser, which treats the remaining positional arguments as input images (lines 147-148; export parser `applets/dataExport/dataExportApplet.py:139-148`). Argument order and the exact batch parser were not read further.
3. **Source selection.** `--export_source` is compared case-insensitively with the workflow's export names (`dataExportApplet.py:257-267`). The names are `"<Probabilities|Simple Segmentation|Uncertainty|Features|Labels|Input> Stage <n>"` with the last stage first, plus `Probabilities All Stages` (`newAutocontextWorkflow.py:58, 124-128`). `probabilities stage 2` selects `Probabilities Stage 2` = the final stage's `HeadlessPredictionProbabilities` (line 302), computed from stage-2 features without the GUI caches (`opPixelClassification.py:430-436`).
4. **Batch lane.** For each input image the batch applet appends a lane, runs the export, and removes the lane (`applets/batchProcessing/batchProcessingApplet.py:110-140`). The new image's data-selection settings (including axis tags) are copied from the **last lane of the project** as a template (lines 180-187), i.e. a training image's settings.
5. **Classifier.** The stored forests are loaded with the project (`applets/base/appletSerializer.py:622-640`; on failure the code only warns "Wasn't able to deserialize the saved classifier" (line 633; what happens next was not traced, but the next point shows a missing classifier is trained from the stored labels); a loaded classifier with more classes than stored labels is also discarded, `pixelClassificationSerializer.py:104-119`). If a classifier is not trained when the batch starts, the workflow logs "A new classifier will be trained for this run" (`newAutocontextWorkflow.py:427-432`; those lines only check the flag and log, and the training itself happens when the prediction first requests the classifier, a path not traced). Which of these happened for these files in the original runs is **unknown**; the files contain trained forests for both stages.
6. **Prediction path** (per image): raw image -> stage-1 features -> stage-1 forest -> x255 truncated to uint8 -> stacked with raw -> stage-2 features -> stage-2 forest. Each stage's forest output is the mean of 100 trees' leaf fractions (section 6).
7. **Cache handling.** Before exporting, the feature caches are bypassed and "freeze predictions" is turned off so the result uses the current labels (`prepare_for_entire_export`, `newAutocontextWorkflow.py:439-455`).

## 12. What the exported file contains

**Source facts**
- **Axis order.** With no `--output_axis_order`, the export uses the image's original axis keys (`lazyflow/.../ioOperators/opFormattedDataExport.py:208-214`). For this workflow the data-selection step reorders inputs to the shortest allowed order that keeps all non-singleton axes, from the list `yxc`, `xyc`, ... (`newAutocontextWorkflow.py:163-174`; `applets/dataSelection/opDataSelection.py:436-481`). A 2-D TIFF page has axes `yx` (`lazyflow/.../ioOperators/opTiffReader.py:95`), so the order is `y, x` and a channel axis is appended (`opReorderAxes.py:103-110`). **Derived, not run:** the exported array is `(y, x, class)`, which agrees with `il.py:53-54` indexing `[:, :, i]`.
- **Class channel order.** The class dimension has one entry per stored label, at index `label - 1`, so index 0 = label 1 (`lazyflow/.../classifierOperators.py:525-528, 599-607`; the forest's classes come from `numpy.unique` of the labels, `classifiers/parallelVigraRfLazyflowClassifier.py:109`). For stage 2 this is `background, cell_boundary, mk, pplt` (order of `LabelNames`; see the training notes' section 4).
- **dtype and scaling.** The export dtype defaults to the input slot's dtype (`opFormattedDataExport.py:156`), which for probabilities is `float32` with a nominal range 0.0 to 1.0 (`classifierOperators.py:526-528`). Normalization is applied only if both `--pipeline_result_drange` and `--export_drange` are given, which sets the four min/max slots (`dataExportApplet.py:126-137, 273-277`; `opFormattedDataExport.py:160-196`); `il.py` passes none. The project also restores saved export settings (range, dtype, axis order, filename format, internal path; `applets/dataExport/dataExportSerializer.py:61-76`), and command-line options override them only when given (`dataExportApplet.py:273-297`). `mouse.ilp` `/Prediction Export` stores only `OutputFilenameFormat` (`{dataset_dir}/{nickname}_{result_type}`), `OutputFormat` (`hdf5`) and `OutputInternalPath` (`exported_data`), plus `StorageVersion`; no range, dtype or axis-order values (read-only check with `notes/inspect_ilp.py`). So, for `mouse.ilp`, the values are written as `float32`, **unscaled** by ilastik. `human.ilp` was not re-checked for this.
- **Container.** HDF5, dataset path `exported_data` (default `OutputInternalPath`, `applets/dataExport/opDataExport.py:65`). The file is written in `'w'` mode after the old file is removed (`opExportSlot.py:244-252`), so a successful run replaces any earlier export of the same name.
- **Filename.** `{dataset_dir}/{nickname}_{result_type}` + `.h5` (default `OutputFilenameFormat`, `opDataExport.py:64`; formed at lines 212-247; extension at `opExportSlot.py:123-128`). `dataset_dir` is the input image's directory, `nickname` is the image file's base name without extension (`dataSelection/opDataSelection.py:187`), `result_type` is `Probabilities Stage 2`. That gives `<image>_Probabilities Stage 2.h5` beside the image, which is exactly what `il.py:37, 49` expects.

**Not read:** skimage's `img_as_uint` (used in `il.py:54`) is outside the ilastik source; its float-to-uint16 scaling is *(background)*, standard behavior for floats in [0, 1].

## 13. Does a headless run change the project file?

- The project file is opened read-write (section 11, item 1).
- The code paths read for this run contain no call that saves the project: `saveProject` is called in `--retrain` handling (`newAutocontextWorkflow.py:420-421, 466-479`), in project creation (`headlessShell.py:56`) and in GUI code, none of which `il.py` triggers. The batch lane is added and removed in memory (`batchProcessingApplet.py:110-140`), and closing only closes the file (`projectManager.py:512-519`).
- **Not shown:** that nothing else writes during loading or serializer code that was not read. **Verdict: no write found in the paths read; not confirmed by running.** A rerun comparing the file hash before and after would settle it (task `ce4` territory).

## 14. Resolved and still-open points from the training notes (section 9 there)

| Point | Status |
|---|---|
| Exported channel order and dtype | **Resolved from source** (section 12): `(y, x, class)` float32 in [0, 1], class index = label - 1; holds for `mouse.ilp` because its stored export settings carry no range, dtype or axis-order override; not run. |
| Why mouse.ilp stores 8 forests while the factory records 4 | **Partly resolved**: option codes decoded and forest count explained by section 7; *why the saved pickle says 4* is still **unknown**. |
| Meaning of stage-1 label names | The code ignores them (section 9). Owner's account: empirical descriptions of what was seen; stage 1 labeled with single-pixel seeds, stage 2 with dense regional strokes (see training notes section 9 for what the file shows). |
| Whether the embedded images match the original TIFs; where originals and ground truth are | Still open (tasks `ce4`, U-1a, U-1b). |
| Whether 1.3.3post2 loads these projects unchanged | **Partly resolved**: for the Autocontext stage-2 input and 8-bit data, equal in the constructs compared (section 10); project loading and the whole file set were not diffed line by line. Unconfirmed by running. |
| Independent review of the notes | Codex review run (see U-4 and VER-3 in `PROJECT.md`); not reviewed by the owner. |
| Tree stopping rule, VIGRA eigenvalue ordering, VIGRA/fastfilters build bundled | Still **unknown** (sections 5, 3, U-5). |
| Whether the headless run saves anything to the project | No write found; unconfirmed (section 13). |
