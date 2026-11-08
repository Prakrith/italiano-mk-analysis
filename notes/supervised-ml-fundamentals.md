# Supervised pixel classification, as used in this pipeline

Companions: `notes/training-and-inference.md` (the files; cited as "the notes") and `notes/ilastik-internals.md` (ilastik source; cited as "the source notes"). The focus is `ilps/mouse.ilp`.

**Tags on statements.**
- *(file)*: read from the `.ilp` or repository files (citations in the notes).
- *(source)*: read in ilastik 1.3.2rc2 / VIGRA source, not run (citations in the source notes).
- *(owner)*: the owner's own account, not checkable in the files.
- *(background)*: general machine-learning explanation, not verified here.
Anything not tagged is a definition or a pointer within these notes. Unknowns stay unknown.

## 1. The whole pipeline in one picture

```
 8-bit grayscale image  (H x W pixels)
        |
        |  STAGE 1
        |  for every pixel: 49 feature values (section 3)
        v
 random forest 1: 100 trees, trained on 172 labeled pixels, 5 classes
        |
        v
 5 maps (one per stage-1 class), values 0..1  --> x255, cut to whole numbers 0..255
        |
        |  STAGE 2
        |  stack: [ raw image, 5 stage-1 maps ] = 6 channels
        |  for every pixel: 49 feature values per channel x 6 = 294
        v
 random forest 2: 100 trees, trained on 285 labeled pixels, 4 classes
        |
        v
 4 maps, values 0..1: background, cell_boundary, mk, pplt  (saved by ilastik as an HDF5 array)
        |
        v   mk/util/il.py: each map -> 16-bit PNG, then the HDF5 file is deleted
 4 PNGs per image  --> CellProfiler (not covered yet)
```

### The same pipeline as a walkthrough

Input: an 8-bit grayscale image, 1 channel. **Stage 1:** for every pixel there are 49 features. There are 6 filters × 7 scales = 42 filter-scale pairs, and 5 are off (every filter except Gaussian smoothing at σ=0.3), which leaves 37. The two eigenvalue filters give 2 features per pair, 12 pairs in all, so 37 + 12 = 49 features per pixel *(file, source)*. Each of the 172 labeled pixels is a training row: its 49 features plus its class label. These rows fit a random forest of 100 trees with 5 classes. For every pixel in the image, the forest outputs 5 scores between 0 and 1, one per class, which makes 5 maps. These are multiplied by 255 and truncated to whole numbers (178.5 becomes 178), giving 8-bit images *(source)*. **Stage 2:** the input is 6 channels (raw + 5 maps). Stage 2 uses the same 37 filter-scale pairs (the stored selection is identical), and each pair is run on every channel. That gives the same 49 features per channel, so 49 × 6 = 294 features per pixel. The number of filter-scale recipes stays 37; only the number of channels they are applied to grows. The 285 labeled pixels, with 4 classes (background, cell_boundary, mk, pplt), fit a second forest of 100 trees. Its output is 4 maps of scores between 0 and 1, saved by ilastik as one array. `il.py` then writes each map as a 16-bit PNG and deletes the HDF5 file (`il.py:58`), so there are 4 PNGs per image, and those go to CellProfiler *(file, source)*. Stage 1's maps are not written to disk; they feed stage 2 inside the same ilastik run *(source)*.

Not known from the files: why 100 trees, and why these filters and scales were chosen.

*(file, source)*: the two stages, the class counts, 49 and 294, 100 trees each, and 172/285 labeled pixels come from the `.ilp` (notes sections 2, 5, 7); the stacking, the 0-255 conversion and the output layout come from the source (source notes sections 9 and 12). Only stage 2's output is exported (`il.py:42`).

## 2. Vocabulary

| Term | Meaning here |
|---|---|
| **Pixel** | one position (y, x) in the image. |
| **Channel** | one 2-D image plane in a stack. A stage's input stack has channels: the raw image has 1, stage 2's input has 6 (raw + 5 stage-1 maps). A stage's output array also has one channel per class, so one class map is one channel. The same word names inputs and outputs; a class is the category, a channel is the plane that holds its map. |
| **Class / label** | a category a person assigns to a pixel while labeling, for example `mk`. Stage 1 has 5 classes, stage 2 has 4. A class is just a number (1, 2, ...) to the software; the name is only for people *(source)*. |
| **Filter** | an operation applied to the whole image that produces a new image, for example Gaussian smoothing or gradient magnitude. Six filters are selected *(file)*. |
| **Scale (σ)** | the scale parameter of a filter, in pixels: the standard deviation of the Gaussian it is built from. It is not a cutoff radius; the kernel reaches several times σ. Seven scales are selected: 0.3, 0.7, 1.0, 1.6, 3.5, 5.0, 10.0 *(file)*. Bigger σ = bigger neighborhood. |
| **Recipe (filter-scale pair)** | one filter at one scale, for example "gradient magnitude at σ=3.5". 37 are switched on in both stages *(file)*. A recipe applied to a channel gives one feature (one value per pixel), or two features for the eigenvalue filters, so 37 recipes give 49 features per channel. |
| **Feature** | one output component of a recipe applied to one channel; it is one input column of the model. Its **feature value** is the number that column holds for one pixel. Per channel there are 49 features (37 filter-scale pairs, 12 of which give two features) *(file, source)*. |
| **Feature vector** | the list of one pixel's feature values: 49 in stage 1, 294 in stage 2. |
| **Training example (row)** | one labeled pixel: its feature vector (the inputs) plus the class the person gave it (the target). Mouse: 172 rows in stage 1, 285 in stage 2 *(file)*. Unlabeled pixels supply no rows and no targets *(source)*, although their intensities still enter the features of nearby labeled pixels. |
| **Decision tree** | a chain of yes/no questions on feature values ("is feature 17 above x?") that ends in a leaf *(background)*. Each leaf stores the class fractions of the training rows that reached it *(source)*. |
| **Random forest** | many trees trained on different random resamples of the rows, each split choosing among a random subset of the features (7 of 49 in stage 1, 17 of 294 in stage 2) *(file, source)*. Here: 100 trees per stage. |
| **Forest-of-forests** | an ilastik/lazyflow detail: the 100 trees are trained in several VIGRA forests (mouse: 8; human: 4) so they can train in parallel, then their trees are averaged as if they were one forest of 100 *(file, source)*. Grouping the same trained trees differently gives the same average; whether a different number of forests would have trained the same trees is not established. In these notes "forest" means a stage's whole 100-tree classifier. |
| **Probability map** | an image whose value at each pixel is the forest's score for one class. See section 5 for why "score" is the safer word. |
| **Stage** | one round of "features -> forest -> maps". |
| **Inference / prediction** | running a trained model on a new image. |
| **Fit / training** | choosing the trees from the labeled rows. In this pipeline it happened in the ilastik GUI *(file: the project holds trained trees; owner: GUI labeling)*. |

*(owner)* Class names such as `white`, `black`, `gray`, `background_cell` in stage 1 were chosen as empirical descriptions of what was seen in the image while labeling. The software ignores the names.

### Where the key numbers come from

| Number | Calculation | What it counts |
|---|---|---|
| 42 | 6 filters × 7 scales | filter-scale pairs available to pick |
| 37 | read from the stored `SelectionMatrix` *(file)* | pairs switched on (5 are off) |
| 12 | counted from the 37 *(file, source)* | selected pairs that are two-output eigenvalue filters |
| **49** | 37 + 12 | **features per channel** (same in both stages) |
| 1 | the raw image | stage 1 input channels |
| **49** | 49 × 1 | **stage 1 feature vector length** |
| 5 | one per stage-1 class | stage 1 output maps |
| 6 | 1 raw + 5 stage-1 maps | stage 2 input channels |
| **294** | 49 × 6 | **stage 2 feature vector length** |
| 4 | background, cell_boundary, mk, pplt | stage 2 output maps |
| **172** | sum over the stored stage-1 label blocks *(file)* | stage 1 training rows (labeled pixels) |
| **285** | sum over the stored stage-2 label blocks *(file)* | stage 2 training rows (labeled pixels) |
| 100 | read from the saved classifier *(file)* | trees per stage (stored as several smaller VIGRA forests, e.g. mouse 13,13,13,13,12,12,12,12) |
| 7, 17 | floor(√49 + 0.5), floor(√294 + 0.5) *(source)* | features each tree considers at a split, stages 1 and 2 |

| | Feature matrix (rows × columns) | Output per pixel |
|---|---|---|
| Stage 1 | 172 × 49 | 5 scores (mean of 100 trees) |
| Stage 2 | 285 × 294 | 4 scores (mean of 100 trees) |

*(file, source)* Each row also has a target (its class label), kept separately from this matrix. Columns (49, 294) come from the filter setup and the channel count. Rows (172, 285) come from the labeling; the two stages' label sets are stored separately (not statistically independent: they come from the same training images), so 285 does not follow from 172. Trees and classes come from the saved classifier and the label names. At prediction time an H × W image gives H × W rows with the same columns, and stage 2's output is H × W × 4. Do not confuse channels with classes: a class is a category, and each class's output map is one channel of the stage's output array. Stage 1's five class maps become five of stage 2's six input channels.

## 3. Features: what the model knows about a pixel

- *(background)* A raw intensity alone often cannot separate a cell interior from a boundary, so pixel classification describes each pixel by filter responses over its neighborhood at several scales. *(file)* The selected filters and scales are in `FeatureSelections`; the file does not show that intensity alone would have failed here.
- Filter families *(file: names; plain-language gloss is background)*: Gaussian smoothing (local average), Laplacian of Gaussian and Difference of Gaussians (blob/edge-like contrast), Gaussian gradient magnitude (edge strength), structure tensor eigenvalues (local orientation strength), Hessian eigenvalues (curvature). The two eigenvalue filters give two features per scale (two feature values per pixel).
- **Nominal and effective scale** *(source, derived by arithmetic, not run)*: ilastik first smooths the image, then applies the filter to the smoothed copy. For the single-Gaussian filters (Gaussian smoothing, Laplacian of Gaussian, gradient magnitude, Hessian eigenvalues), and treating the Gaussians as ideal (ignoring finite, discretized kernels), the total is the nominal σ for scales above 1, and √2 × σ for scales at or below 1 (here 0.3, 0.7 and 1.0), for example about 0.42 for the nominal 0.3. This does not reduce to one number for two filters: Difference of Gaussians subtracts two Gaussians (the second at 0.66 of the first's scale), and the structure tensor smooths products of gradients again at an outer scale of 0.5 of its inner scale (`opPixelFeaturesPresmoothed.py:150-164`, 1.3.2rc2). A reimplementation must copy the recipe, not the nominal σ (source notes section 3).
- Larger σ means the number reflects a larger neighborhood, so a pixel's description includes context *(background)*.
- **Stage 2 features are computed on all 6 channels** *(source, file)*: each channel contributes 49 features. The stored column order is not six blocks of 49: it runs filter, then scale, then channel (Gaussian smoothing σ=0.3 on channels 0 to 5, then σ=0.7 on channels 0 to 5, and so on), and within an eigenvalue pair channel then output component. Five of the six channels are stage 1's view of the image (the sixth is raw), and scales go up to σ=10 pixels, so stage 2 can use stage 1's guesses about the surroundings. A reimplementation must reproduce this column order to use the saved trees.
- Features are computed from float32 copies of the image; there is no extra normalization step *(source)*.

## 4. Training examples and targets

- Mouse stage 2: 285 examples (81 background, 55 cell_boundary, 92 mk, 57 pplt); stage 1: 172 examples (5 classes) *(file: notes section 7; equals the forests' `row_count_`)*.
- Most pixels of the nine training images are unlabeled *(file: 172 and 285 labeled pixels against 1040 × 1408 pixels per image)* and give no rows *(source)*. The forest never sees the image as a whole during fitting: it sees a table with one row per labeled pixel *(source)*. The neighborhood of each labeled pixel still shapes its features.
- *(owner)* Stage 1 was labeled with single-pixel seeds to define class boundaries precisely and limit class bleeding; stage 2 with dense regional brush strokes to give morphological context and spatial continuity. *(file)* Stored label blocks hold a median of 5 labeled pixels per block in stage 1 and 8 in stage 2 (maximum 18 and 24), so nothing in the file shows dense regional strokes. Block geometry is storage, not brush shape, so this does not contradict the owner's account; it just does not confirm it.
- *(background)* Neighboring pixels of the same cell are strongly correlated, so 285 rows carry less information than 285 independent samples.
- The two stages have **separate label sets**; stage 1's labels are not copied to stage 2 automatically *(source)*.

## 5. The forest: from trees to a map value

*(source, VIGRA `Version-1-11-1` stand-in for the bundled build; see U-5)*
- Each tree is trained on a random sample of the labeled rows, drawn with replacement and as large as the training set (a bootstrap sample). At each split it considers 7 (stage 1) or 17 (stage 2) randomly chosen features and picks the split with the best Gini criterion. Class stratification is off.
- A leaf stores the class fractions of the training rows that reached it during fitting (the rows are a bootstrap sample, so a row can count more than once).
- **To predict a pixel**, each of the 100 trees sends the pixel to one leaf; the output for a class is the **mean of the 100 leaves' fractions for that class**. It is not a count of tree "votes", though the two are close when leaves are nearly pure.
- Pictures of a tree, a prediction and the averaging: `notes/pictures.md`, pictures 1 to 4.
- *(illustration, made-up numbers)* A leaf reached by 10 training rows, 7 labeled `mk`, 2 `pplt` and 1 `background`, stores (background 0.1, cell_boundary 0.0, mk 0.7, pplt 0.2). That is the tree's contribution for any pixel that lands there. If the 100 trees' `mk` fractions average 0.62, the pixel's `mk` score is 0.62. Each tree scores all classes; there is no target at prediction time (a target is the label on a training row).
- The classes sum to 1 at each pixel (unless a feature was NaN, then all zeros).
- *(source)* The `.ilp` stores no accuracy figure although ilastik computes an out-of-bag error while training.
- **Are these probabilities?** The numbers are in [0, 1] and sum to 1, so they are model probability estimates in form. A *calibrated* estimate would also satisfy "among pixels with score 0.7, about 70% really belong to the class". That has not been tested for these models: calibration is **not established**. Until it is, read them as relative scores. *(background)* Forests trained on few, correlated rows are often over- or under-confident.
- Unknown: the tree stopping rule and depth limit; the eigenvalue output order; whether VIGRA or `fastfilters` computed the features in the binary used.

## 6. Fit versus inference

| | Fit (training) | Inference (prediction) |
|---|---|---|
| Where | the ilastik GUI *(owner)* | `RunIL.process` calls the ilastik executable headless, per image |
| Input | labeled pixels and their features | a whole new image; features at every pixel |
| What happens | trees are chosen from the labeled rows | each stage's 100 trees score every pixel; stage 1's scores feed stage 2 |
| Output | trees stored in the `.ilp` | the 4-class stage-2 array |
| Changes the model? | yes | the executable opens the project read-write (no `--readonly`), but no save was found in the code paths read; **not confirmed by running** *(source)* |

- *(file)* `il.py` contains no fitting step; the trained trees are in the `.ilp` and the wrapper hands that file to ilastik.
- *(source)* If a stored classifier cannot be loaded or is missing, ilastik trains one from the stored labels when the batch run begins (source notes section 11). Which happened in the original runs is unknown.
- *(source)* A headless batch run takes the axis settings of a new image from the **last image stored in the project**.

## 7. Probabilities versus final decisions

- ilastik writes `(y, x, class)` `float32` values in 0..1 to `<image>_Probabilities Stage 2.h5`, dataset `exported_data`, class index = label - 1; for `mouse.ilp` nothing rescales the values *(source; file for the export settings)*.
- `il.py` makes **no hard decision**. It converts each class map to a 16-bit PNG with `skimage.img_as_uint` (1.0 becomes 65535) *(file; the scaling rule is background)*.
- A final decision would be an argmax over classes or a threshold on one class *(background)*; both discard the relative scores (how close the classes were). Where the maps become objects is CellProfiler's job (tasks no9, hgf): unknown until those files are inspected.

## 8. Autocontext (two stages)

- *(file)* Workflow `AutocontextTwoStage`. Stage 1: 5 classes, 49 inputs. Stage 2: 4 classes, 294 inputs.
- *(source)* Stage 2's input is the raw image plus stage 1's five maps, converted by `floor(255 × value)` to 0-255 integers. Stage 1 sees only the raw image.
- *(background)* Why: stage 2 can use the neighborhood's guessed classes ("pixels around me are probably boundary") to correct stage 1's mistakes.
- *(source)* Stage 2 uses stage 1's maps only as 5 numeric channels; their class names play no role.
- *(source)* Stage 2 is trained on features computed from stage 1's output at stage 2's labeled pixels. *(hypothesis, not tested)* If stage 1 also trained on pixels or images that overlap these, its scores there are likely more confident than on new images, and stage 2 may over-trust stage 1. Neighboring pixels and whole images are correlated, so exact coordinate overlap is not needed for the concern; whether it matters here is unmeasured.
- *(source)* ilastik 1.3.3post2 changes this conversion code but gives the same result for 8-bit images; all stored images are 8-bit *(file)*.

## 9. Generalization: does it work on new images?

- *(background)* A model can match its labeled pixels and still fail on new images. The only reliable test is data it never trained on.
- *(file)* The `.ilp` holds trees, labels, embedded training images and settings; nothing that looks like a held-out set or accuracy measure, and no independent ground truth has been located (U-1b). **How well this classifier generalizes is unknown.**
- Risk factors (observations, not conclusions) *(file)*: few labeled pixels (285 in stage 2); uneven classes (the mouse `dmso` image has 0 `mk` and 2 `cell_boundary` pixels); nine training images, all 1040 x 1408 and 8-bit. *(file, source)* The wrapper does not enforce an image size, but the ilastik workflow accepts only 8-bit input (1.3.2rc2).
- *(background)* More labels where the model is wrong improve fit on those cases; they do not by themselves measure generalization.

## 10. Coverage table (R-2)

| R-2 item | Section | Basis |
|---|---|---|
| Training examples and targets | 2, 4 | file counts; row construction from source |
| Features | 2, 3 | file lists; computation from source; filter glosses background |
| Fit versus inference | 6 | file for `il.py`; source for ilastik behavior; headless-save question unconfirmed |
| Probabilities versus final decisions | 5, 7 | source for the averaged output and export layout; calibration unknown |
| Autocontext | 1, 8 | file for the structure; source for the wiring; leakage is a hypothesis |
| Generalization | 9 | absence of evidence only |

## 11. Teach-back questions (VAL-1), rewritten (eight)

Answer from memory, in your own words; "I don't know" is a valid answer and shows what to re-read. A reference answer sits under each question, so cover it until you have written yours. Each answer is based on the owner's first draft; "Draft correction" lines say what was changed. What the files and source do not settle is collected in "Still unknown" at the end of this section.

1. **The picture.** Describe what goes into and comes out of each stage: how many channels, what kind of values, and what the final output files are.
   - *Answer:* the walkthrough in section 1, below the picture. It is the single copy.
2. **One training row.** For mouse stage 2, what are the columns of one training row, what is its target, and how many rows are there? Why are the unlabeled pixels not rows?
   - *Answer:* Each training row is one labeled pixel. It has 294 feature columns (49 features on each of the 6 channels) plus a target: the single class painted at that pixel (background, cell_boundary, mk or pplt). There are 285 rows. Unlabeled pixels give no rows because they have no target to learn from, though their intensities still shape the features of nearby labeled pixels.
   - *Draft correction:* the target is one class label per row. The maps and scores are the model's output, not the target.
3. **One feature.** Pick "Gaussian gradient magnitude at σ = 3.5". What value (feature value) does it give for a pixel, what does the scale change, and why does stage 2 have six times as many features as stage 1?
   - *Answer:* It blurs the channel with a Gaussian whose standard deviation is 3.5 pixels, then measures how steeply brightness changes at each pixel. The feature value is that steepness (gray levels per pixel): near 0 in a flat area, large on an edge. The scale σ is the spread of the Gaussian weighting, not a hard neighborhood (the kernel reaches several σ). A larger σ generally suppresses fine detail and broadens edge responses. This is the idealized reading; section 3 gives the caveats. Stage 2 has 6 input channels (1 raw + 5 stage-1 scores) and the same 37 recipes run on each, giving 49 features per channel and 49 × 6 = 294. This recipe is applied to six channels.
4. **From trees to a map value.** A pixel passes through 100 trees. What does each tree contribute, how is the pixel's value for `mk` computed, and why is it safer to call it a score than a probability?
   - *Answer:* Each tree sends the pixel to one leaf, and the leaf stores the class fractions of the training rows that reached it. That is the tree's contribution: a fraction for each of the 4 classes. The pixel's `mk` value is the mean of the 100 trees' `mk` fractions, and the four class values sum to 1. The values are model probability estimates in form (between 0 and 1, summing to 1), but calibration (among pixels scoring 0.7, about 70% really are `mk`) has not been tested for these models, so "score" is the safer word.
   - *Draft correction:* a target belongs to training rows. At prediction every tree gives a fraction for all four classes.
   - *Pictures:* `notes/pictures.md`, pictures 1 to 4.
5. **What stage 2 adds.** What does stage 2 receive that stage 1 does not, why might that help with boundaries, and what is the possible problem with training stage 2 on stage 1's output at the same pixels?
   - *Answer:* Stage 2 receives the raw image plus stage 1's five score maps (scaled by 255 and truncated to 0 to 255), so 6 channels *(file, source)*. Stage 1 sees only the raw image. Stage 2 runs the same 37 recipes on all 6 channels, so it can compute things like the average of one stage-1 score map around a pixel. This may help boundaries *(background reasoning)*: if stage 1 slips at one pixel of a structure but its neighbors score high for the same class, stage 2 can use the neighbors' scores to correct it. The possible problem *(hypothesis)*: if stage 1 was trained on the same images or pixels that stage 2 trains on, stage 1's scores there are probably more confident than on new images, so stage 2 may trust stage 1 too much on new images.
   - *Picture:* `notes/pictures.md`, picture 5.
6. **Model versus pipeline.** What does the headless call produce, which step turns it into PNGs, and which decision still has to be made before you have a segmentation?
   - *Answer:* The ilastik headless call runs the saved model on a new image and writes one HDF5 array of stage-2 scores, H × W × 4, 32-bit floats between 0 and 1 *(source)*. `il.py` converts each class map to a 16-bit PNG and deletes the HDF5 file *(file)*, so the 4 PNGs are score maps, not a segmentation. The decision still to be made is how to turn scores into a hard answer per pixel: take the class with the highest score (argmax), or threshold one class map (for example `mk` > 0.5). `il.py` makes neither choice. A 0.5 threshold is just a rule; reading it as "more likely than not" would require calibrated scores, which is not established. A later step turns the per-pixel mask into individual objects.
   - *Draft correction:* "decision" means turning scores into a hard per-pixel answer.
   - *Picture:* `notes/pictures.md`, picture 7.
7. **Evidence.** What would you need, beyond the `.ilp` files, to claim the classifier works on a new experiment?
   - *Answer:* A test set: images never used to fit the trees or to choose labels, filters or settings, with hand-made labels as ground truth that are independent of the training labels. They should come from new experiments or images, not neighboring pixels of the training images, because neighboring pixels are correlated and would make the result look better than it is *(background)*. Then compare the model's output with that ground truth using a measure that matches the use (for example per-pixel agreement per class, and agreement on objects if the end goal is object counts). If the scores will be read as probabilities, check calibration on the same set. Labels added where the model is wrong improve the fit, but used that way they stop being a test.
8. **Fit versus inference.** What does fitting change, what does the `.ilp` store, what does the headless call do with it, and in what case might ilastik train new trees at run time? What is still unknown about whether the project file gets saved?
   - *Answer:* Fitting is choosing the trees from the labeled rows, which changes the model. Inference applies the already chosen trees to new pixels, which does not change the model; saving the trees is what allows fitting once and predicting many times. The same feature recipes, in the same column order, must be used at fit and at inference, because the trees ask questions about specific columns. The `.ilp` stores the labels, the feature settings and the trained trees *(file)*. The headless call loads it and runs both stages on a new image *(source)*, and `il.py` contains no fitting step *(file)*. ilastik-specific detail: if a stored classifier is missing or cannot be loaded, ilastik trains a new one from the stored labels when the batch run begins *(source)*. The project is opened read-write, but no save was found in the code paths read, so whether a headless run changes the project file is not confirmed *(source, not run)*.
   - *Picture:* `notes/pictures.md`, picture 6.

### Still unknown (not needed to answer the questions above)

- Why 100 trees, and why these filters and scales.
- Whether stage 2 actually relies on the neighbor-score features (variable importance was not saved, although the stored trees could be inspected), and whether the stage-1 to stage-2 overlap concern matters here.
- Whether the scores are calibrated.
- Whether a headless run ever saves the project file, and which of the original runs, if any, retrained a classifier.
- How the PNG maps become objects (CellProfiler, tasks no9 and hgf).
- Where independent ground truth is, and whether it exists (U-1b in `PROJECT.md`).
