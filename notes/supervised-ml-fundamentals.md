# Supervised pixel classification, as used in this pipeline

Companion to `notes/training-and-inference.md` (cited below as "the notes"). The focus is `ilps/mouse.ilp`; numbers come from the notes and were read from that file.

**Two kinds of statement.** Pipeline facts are marked *(file)* and are backed by the notes' citations. General machine-learning background is marked *(background)*: it is standard explanation, not something verified from this repository, and ilastik-internal behavior is not verified here. Anything unverified in the notes stays unknown here.

## 1. The task in one paragraph

Given a phase-contrast image, decide for every pixel whether it is background, cell boundary, megakaryocyte (`mk`) or proplatelet (`pplt`). The result is four probability images per input. CellProfiler later turns those into objects (out of scope here). Learning means: a person marks a few pixels with the right class, and a model learns a rule that labels all the others *(file: `PixelClassification01/LabelNames`, `mk/util/il.py:16`)*.

## 2. Training examples and targets

- **Example** = one labeled pixel. **Target** = the class the person gave it (stage 2: 1 background, 2 cell_boundary, 3 mk, 4 pplt) *(file: `known_labels` = 1..4)*.
- Mouse stage 2 has 285 examples: 81 background, 55 cell_boundary, 92 mk, 57 pplt *(file: notes section 7; equals `row_count_` of the trained forests)*. Stage 1 has 172 (5 classes).
- Most pixels of the nine training images are unlabeled and are not examples. Labeled pixels are stored as small rectangular blocks (`blockSlice` is storage geometry, not necessarily the shape of the brush strokes). `docs/Setup.md:10-11` describes the intended procedure (label irregular and uncertain areas); the files do not show that the labels were actually drawn that way.
- *(background)* The model never sees "the image" as a whole during fitting; it sees a table with one row per labeled pixel: input columns (features) and one target value. Many pixels of the same cell are strongly correlated, so 285 rows carry less information than 285 independent samples would.

## 3. Features: what the model sees about each pixel

- A raw intensity alone cannot tell a cell interior from a boundary, so each pixel is described by filter responses computed in its neighborhood at several scales *(file: `FeatureSelections`)*. Scales (σ, in pixels) are 0.3, 0.7, 1.0, 1.6, 3.5, 5.0, 10.0.
- The six filter families selected are Gaussian smoothing (local average), Laplacian of Gaussian and Difference of Gaussians (blob/edge-like contrast), Gaussian gradient magnitude (edge strength), structure tensor eigenvalues (local orientation strength) and Hessian eigenvalues (curvature) *(file: `FeatureIds`; the plain-language gloss is background)*.
- 37 filter-scale pairs expand to **49 numbers per pixel** in stage 1 *(file: `column_count_`)*.
- Larger σ means the number reflects a bigger neighborhood: a pixel's description includes context, which is how a pixel-wise classifier can separate a cell body from similar-looking background.
- Stage 2 uses **294 numbers per pixel** = the same 49 filters on 6 input channels *(file; the notes mark the composition as "consistent with" raw image plus 5 stage-1 probability channels, not as a stored field)*.

## 4. The classifier: a random forest

- *(file)* A VIGRA random forest with 100 trees in total (mouse stores them as 8 forests of 13 or 12 trees; reason for 8 unknown).
- *(background)* A decision tree asks a chain of yes/no questions about the feature values ("is the σ=3.5 Hessian value above x?") and ends in a class. A forest trains many trees, each on a random resample of the examples (the file records sampling with replacement) and with a random subset of features considered at each split (`actual_mtry_` = 7 of 49 in stage 1, 17 of 294 in stage 2). Averaging many varied trees is more stable than one tree.
- *(background)* The forest's output for a pixel is the fraction of trees voting for each class. That is the simplified picture. Real forest implementations may instead average per-tree class distributions, and the notes do not verify how the VIGRA forest in these files aggregates. Whether the resulting numbers are calibrated probabilities is **not established** here; they should be read as scores until tested against held-out data.
- Settings that control model complexity beyond these (tree depth limits, random seed) are not stored: unknown.

## 5. Fit versus inference

| | Fit (training) | Inference (prediction) |
|---|---|---|
| When | in the ilastik GUI, interactively | `RunIL.process`, headless, per image |
| Input | labeled pixels + their features | whole new image; features computed for every pixel |
| Output | the trees, saved inside the `.ilp` (`ClassifierForests/Forest*/Tree_*`) | one probability image per class |
| Changes the model? | yes | the wrapper contains no fitting step; whether the ilastik executable writes anything back to the `.ilp` is unverified |

*(file: notes sections 5 and 6; `il.py:40-46` calls `--headless --export_source=probabilities stage 2 --project=<ILP>`)*. The repository code contains no explicit fitting operation; the trained trees are stored in the `.ilp` and the wrapper hands that file to an external executable. What the executable does with the project beyond predicting (for example saving) is not verified. Training was done interactively in the GUI (`docs/Setup.md:3-11`), per the repository's own instructions.

## 6. Probabilities versus final decisions

- `il.py` reads an array `exported_data` and treats axis 2 as one channel per class *(file: `il.py:51-53`; the dtype and channel order are assumptions of that code and unverified; the float [0, 1] range is what `img_as_uint` expects)*. `il.py` writes each channel to a PNG with `skimage.img_as_uint` *(file)*, so a value of 1.0 becomes 65535.
- **Observed:** `il.py` makes no hard decision. It does not take an argmax or apply a threshold; the output is four soft maps `<name>_<label>_prbstg2_<i>.png`.
- Where, if anywhere, the soft maps are turned into object masks is CellProfiler's job (tasks no9, hgf) and is **unknown** until those files are inspected.
- *(background)* A "final decision" would be argmax over classes or a threshold on one class; both discard the information on how sure the model was.

## 7. Autocontext (two stages)

- *(file)* The workflow is `AutocontextTwoStage`. Stage 1 is trained on the image alone (5 classes). Stage 2 is trained with labels from a different class set (4 classes) and has 294 input columns instead of 49.
- *(background)* Idea: stage-1 probability maps are fed to stage 2 as extra input channels, so stage 2 can use the neighborhood's predicted classes (for example "pixels around me are probably boundary") and clean up stage-1 mistakes. The notes' arithmetic (6 channels) fits this; the files do not state it.
- *(file)* Only the stage-2 output is exported (`il.py:42`), and the stage-2 labels are a separate label set from stage 1 (`PixelClassification01/LabelSets`; `docs/Setup.md:11` describes labeling stage 2 separately).
- Observed oddity: stage 1 and stage 2 use different label sets (5 vs 4 classes, different names); how stage 1 outputs map onto stage 2 is not stored: unknown.

## 8. Generalization: does it work on new images?

- *(background)* A model can match the labeled pixels perfectly and still fail on new images, because the labeled pixels are the only evidence it had. The only reliable test is data the model never trained on.
- *(file)* In the inspected `.ilp` files, nothing that looks like a held-out set or an accuracy measure is stored (the file holds the trees, the labels, the embedded training images and settings), and no independent ground truth has been located (U-1b). So **how well this classifier generalizes is unknown**.
- Risk factors visible in the notes (stated as observations, not conclusions): few labeled pixels (285 stage-2 mouse examples); uneven classes (for example the mouse `dmso` image has 0 `mk` and 2 `cell_boundary` pixels); nine training images, all 1040 x 1408 and 8-bit (the wrapper itself does not enforce an input size).
- *(background)* More labels drawn where the model is wrong (what `docs/Setup.md` describes) improves fit on those cases; it does not by itself measure generalization.

## 9. R-2 coverage and teach-back

| R-2 item | Section | Verified against files? |
|---|---|---|
| Training examples and targets | 2 | Yes (notes 5, 7) |
| Features | 3 | Yes for lists and counts; filter glosses are background |
| Fit versus inference | 5 | Partly: `il.py` has no fitting step; the external executable's behavior is unverified |
| Probabilities versus final decisions | 6 | Partly: no decision step in `il.py`; export dtype/order unverified |
| Autocontext | 7 | Partly: stage structure yes; use of stage-1 outputs is background |
| Generalization | 8 | Absence of evidence only (no held-out data stored) |

Teach-back questions for the owner (VAL-1), to answer without the code open:

1. What is one training example in this pipeline, and how many does mouse stage 2 have?
2. Why does each pixel get 49 numbers, and what does a larger σ add?
3. What is stored in the `.ilp` after training, and what does the headless call change?
4. Why are the four PNGs not yet a segmentation? What decision is missing?
5. What does the second Autocontext stage add, and what in the files supports that?
6. What evidence would you need to claim the classifier generalizes to a new experiment?
