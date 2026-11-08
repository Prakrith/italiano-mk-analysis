# Pictures

Visual explanations for `notes/supervised-ml-fundamentals.md`. All numbers, feature names and thresholds in the pictures are made up for illustration unless stated; the facts they illustrate are tagged in the main notes. Add new pictures at the end.

## Picture 1. A tree is yes/no questions on feature values, ending in a leaf

Section 5 of the main notes; VAL-1 question 4.

```
              pixel's 294 feature values
                         |
          gradient magnitude σ=3.5 (raw) > 12 ?
              no /                  \ yes
                /                    \
   stage-1 `white` map, smoothed        LEAF C
   at σ=1.6 > 140 ?
        no /      \ yes
          /        \
      LEAF A      LEAF B
```

During fitting, the training rows that reached each leaf are counted (the rows are a bootstrap sample, so some appear more than once), and the leaf stores their class fractions. Made-up counts:

```
LEAF A: 20 rows -> 18 background, 2 cell_boundary
LEAF B: 10 rows ->  7 mk, 2 pplt, 1 background
LEAF C:  8 rows ->  6 cell_boundary, 2 background
```

Only these stored fractions decide what a leaf says. The tree was built so that its leaves are mostly one class.

## Picture 2. Prediction: a pixel walks down one tree and reaches one leaf

```
 new pixel (294 values)
        |
   question 1: yes  ---------------> LEAF C   (this pixel ends here)
```

The leaf's class fractions are this tree's contribution for this pixel. Had the pixel reached LEAF B instead:

```
 LEAF B  ->   background   cell_boundary    mk    pplt
                 0.1           0.0          0.7    0.2
```

That is one tree's four fractions. It is not a decision; it is the mix of training rows in that leaf.

## Picture 3. The 100 trees disagree, then you average

The trees differ because each is trained on a different random resample of the labeled rows, and each split picks from a random subset of the features (17 of 294 in stage 2). *(source)* The same pixel therefore lands in different leaves in different trees. The `mk` column for one pixel, showing 5 of the 100 trees:

```
 tree  1   leaf says mk = 0.70   |#######     |
 tree  2   leaf says mk = 0.50   |#####       |
 tree  3   leaf says mk = 0.90   |#########   |
 tree  4   leaf says mk = 0.30   |###         |
 tree  5   leaf says mk = 1.00   |##########  |
  ...        (95 more)
 ----------------------------------------------
 average over all 100 trees  =   0.62    <- the pixel's mk score
```

The same averaging runs for background, cell_boundary and pplt, and the four averages sum to 1. Those are the pixel's four scores; the four maps are those scores at every pixel. Averaging many trees smooths out the quirks of any single tree *(background)*.

## Picture 4. Why "score" and not "probability"

```
Score of 0.62 for mk at a pixel.

What it IS:      the average of what 100 trees' leaves said.
                 Higher = the model leans more toward mk here.

What it is NOT (not shown): "62% of pixels like this really are mk".
                 That claim is called calibration.
                 There is no test of it for these models. The forests were
                 trained on only 285 (stage 2) correlated pixels, so over- or
                 under-confidence is plausible.
```

A test would be: collect pixels that scored about 0.6, check against trusted ground truth how many really are `mk`. If about 60%, the score is calibrated around that value for that class; a full check covers all scores and classes. No such evaluation has been found, and no independent ground truth has been located (U-1b in `PROJECT.md`).

## Picture 5. What stage 2 sees that stage 1 does not

VAL-1 question 5. A made-up row of 7 pixels. Imagine that one stage-1 class, here `white` (the owner's empirical label name, so its real meaning is not assumed), happens to trace a continuous line. Stage 1's `white` score at each pixel is shown on the 0 to 1 scale, and below it the 0 to 255 values that stage 2 actually receives (score × 255, truncated):

```
 pixel position:          1     2     3     4     5     6     7
 raw image:             dark  dark  dark  light  dark  dark  dark
 stage 1 white score:    0.9   0.9   0.8   0.2   0.9   0.8   0.9
 as stage 2 receives:    229   229   204    51   229   204   229
                                            ^
                                     stage 1's slip
```

Pixel 4 looks a little different in the raw image, so stage 1 scored it low; its neighbors scored high. Stage 2 can compute features on that stage-1 channel, for example "Gaussian smoothing at σ=3.5 of that map", the average `white` score around each pixel:

```
 smoothed stage-1 white map at pixel 4  ~  0.7  (about 178 of 255): neighbors score high
```

If the stage 2 labels taught the forest that "raw looks odd, but the surroundings score high for this class" usually means that class, it can score pixel 4 accordingly. That would correct stage 1's slip.

```
 STAGE 1 sees:  raw image around the pixel
 STAGE 2 sees:  raw image around the pixel
              + stage 1's guesses (5 score maps) around the pixel
```

That stage 2 receives and filters the stage-1 maps is a source and file fact. That this helps with boundaries is background reasoning, untested here. Which of the 294 features the trees use was not examined: variable importance was not saved in `mouse.ilp` (disabled in the stored factory), although the stored trees could be inspected.

## Picture 6. Fit versus inference

VAL-1 question 8. Fitting changes the model; inference only applies it.

```
 FIT  (once, in the ilastik GUI)               INFERENCE  (each new image, headless)

 painted pixels (172 / 285 labeled)            new image (H x W)
        |                                              |
 features at those pixels  <-- same recipes -->  features at EVERY pixel
        |                                              |
 rows: feature values + the class I painted            |
        |                                              |
 choose the 100 trees ---- saved in the .ilp ---->  saved trees score each pixel
                                                       |
                                                 4 scores per pixel
```

The same feature recipes, in the same column order, must be used at both ends. The trees ask questions about specific columns, so a different recipe or order would make them ask about the wrong features.

## Picture 7. From scores to a decision

VAL-1 question 6. Made-up scores for two pixels. `il.py` writes the scores as 16-bit PNGs and makes no decision.

```
                     background  cell_boundary    mk    pplt
 pixel A                 0.10         0.20        0.60   0.10
 pixel B                 0.10         0.15        0.40   0.35

 rule                        pixel A        pixel B
 --------------------------------------------------
 highest score (argmax)        mk             mk
 mk score > 0.5                mk           not mk
 mk score > 0.7              not mk         not mk
```

Different rules give different segmentations from the same scores. A 0.5 threshold is just a rule; reading it as "more likely than not" would require calibrated scores, which has not been shown for these models. In the legacy pipeline, `pipelines/mouse.cppipe` (CellProfiler) applies a manual threshold of 0.5 to the opened mk map minus the background and pplt maps (clipped to 0 to 1), then identifies objects *(file)*; see `notes/cellprofiler-and-rules.md` for the outline.
