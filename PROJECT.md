# Project record

Tasks live in Beads, in this repository's `.beads/` directory, and this record is `PROJECT.md` at the repository root. The repository is public, so write both for publication.

## Objective

Phase 1 (now): understand how the legacy supervised-ML segmentation and classification pipeline is trained and how inference runs, from the code and the ilastik project files. The data flow and the CellProfiler stages come after that. Phase 1 also covers how the underlying tools work internally (ilastik pixel classification and Autocontext, the VIGRA random forest and filters), read from their source, because the owner wants to know what the headless call does before reimplementing it. Phase 2 (later, separate scope): reimplement it with contemporary techniques that improve segmentation and classification.

## Intended use

Owner's learning and planning. The reimplementation in Phase 2 would analyze phase-contrast TIF time-lapses of megakaryocyte (MK) and proplatelet (pplt) differentiation.

## Requirements

- **R-1.** A written explanation of training and inference in the legacy pipeline, covering both `ilps/mouse.ilp` and `ilps/human.ilp`: features and scales, labels, classifier, Autocontext stages and training annotations (from the `.ilp` files), and the headless inference call and probability outputs (from `mk/util/il.py`), citing files and lines. "Annotation counts" means labeled pixels per class, per image and per stage. Image references stored in a file are kept separate from images actually available.
- **R-2.** A written explanation of the supervised-ML fundamentals behind that training and inference, at a level the owner can explain. Coverage list: training examples and targets; features; fit versus inference; probabilities versus final decisions; Autocontext; generalization.
- **R-5.** A written explanation, from the source code of the tools the pipeline calls, of how ilastik computes features, trains and applies the random forest, runs the Autocontext stages and writes the export, at the versions the `.ilp` files and `config.ini` name (ilastik 1.3.2rc2 and 1.3.3post2), citing source file, line and version tag. CellProfiler internals are outside this requirement (see R-4).
- **R-4.** (Lower priority, after R-1 and R-2.) The end-to-end data flow and the CellProfiler and CPA-rules stages, citing the files that define each step.
- **R-3.** (Deferred until training and inference are understood.) A list of the pipeline's limitations and open questions, and candidate modern methods for Phase 2. Observed facts, open questions and hypotheses are kept in separate lists; every candidate method is a hypothesis until tested.

## Criteria

Status is `open`, `satisfied`, `not satisfied`, or `not applicable` with a reason.

| ID | Type | Traces to | Method | Evidence | Status |
|---|---|---|---|---|---|
| VER-1 | Verification | R-1 | Every R-1 topic is covered for both `mouse.ilp` and `human.ilp`. Information the files do not show is recorded as unknown, never inferred from ilastik defaults. HDF5 evidence cites group, dataset or attribute paths; code evidence cites file and line. The `.ilp` label order is reconciled with `LABEL_LIST` in `mk/util/il.py` | `notes/training-and-inference.md` covers the R-1 topics for both files, with the read-only inspection script `notes/inspect_ilp.py`; Codex reviewed it twice (U-4). Owner decision 2026-11-07: narrowed to R-1 (R-4 moved to VER-4) and closed without an owner spot-check, because the owner wrote the pipeline and the learning focus is the supervised-ML notes | `satisfied` |
| VER-2 | Verification | R-2 | The R-2 coverage list is checked item by item against the notes; claims about the `.ilp` and rules files come from inspecting those files, not from memory | Revised 2026-11-06 using the source notes: `notes/supervised-ml-fundamentals.md` (pipeline picture, vocabulary, statements tagged file/source/owner/background, coverage table); Codex review run 2026-11-06 (2 P1, 6 P2, 1 P3 findings, all fixed in the notes, including the stage-2 column order and the effective-scale formula); a second Codex review 2026-11-07 of the pictures, the VAL-1 answers and the vocabulary (1 P1, 7 P2, 1 P3 findings, fixed; the fixes are not re-reviewed); not yet checked item by item by the owner Coverage table checked item by item 2026-11-07: all six R-2 items map to existing sections; two Codex reviews (U-4); not checked item by item by the owner. | `satisfied` |
| VER-3 | Verification | R-5 | Each claim about ilastik, lazyflow or VIGRA behavior cites a source file and line at a named version tag or commit; behavior that cannot be found in that source is recorded as unknown; differences between the two ilastik versions are noted; the unknowns in `notes/training-and-inference.md` (export channel order and dtype, option codes, forest count) are each resolved or still marked unknown | Drafted: `notes/ilastik-internals.md` (sections 1 to 14) cites file, line and tag; Codex review of the source notes run 2026-11-06 (5 findings, fixed); no citation spot-check by the owner yet. Resolved from source: option codes, channel order and dtype of the export, Autocontext input composition. Still unknown: why mouse's saved factory says 4 forests, tree stopping rule, eigenvalue output order, bundled VIGRA/fastfilters build, whether a headless run ever writes the project (no write found) Owner decision 2026-11-07: closed without an owner citation spot-check, because `notes/ilastik-internals.md` is reference material and the owner's learning focus is the supervised-ML notes; every unknown stays recorded as unknown (see U-5) | `satisfied` |
| VER-4 | Verification | R-4 | R-4 steps name the file and line or module that implements them; owner spot-checks against the files | Not done as a whole. A quick read-only pass on `pipelines/mouse.cppipe` and `pipelines/cpa_rules/mouse_rules.txt` (2026-11-07) matches the owner's account in outline (module list and settings recorded in tasks no9 and hgf); no line-level citations yet Owner decision 2026-11-07: R-4 is not pursued further, because the owner wrote the pipeline and chose to stop; the outline from the quick pass is in `notes/cellprofiler-and-rules.md` | `not applicable` |
| VAL-1 | Validation | Intended use | Teach-back: the owner explains the R-2 concepts and the pipeline from the notes without the code open | Eight rewritten questions in `notes/supervised-ml-fundamentals.md` section 11; the owner answered all eight questions once (2026-11-07); slips on the training target (questions 2 and 4), the meaning of "decision" (question 6) and fit versus inference (question 8) were corrected in the reference answers under each question. Closed by owner decision | `satisfied` |

## Decisions

- Tasks and this record live in the public code repository, so their text is written to be published; nothing private is recorded in them.
- Static inspection of the `.ilp` and `.cppipe` files must not depend on the legacy tools running.
- Missing information is recorded as unknown, not inferred from ilastik defaults.
- Candidate modern methods (R-3) wait until training and inference are understood.
- Further work focuses on `mouse.ilp`. `human.ilp` is already covered in the notes; it is an interchangeable project file made for human-megakaryocyte images (owner statement), so it gets no further study.
- 2026-11-05, owner decision: study the internals of ilastik and VIGRA from source (R-5), not only the wrapper, as the step before Phase 2. Source is cited by file, line and version; no third-party source is copied into this repository beyond short quotations.
- The VAL-1 teach-back questions are rewritten after the source findings, because several of the first set were ambiguous.
- 2026-11-07, owner decision: the ilastik source notes (`notes/ilastik-internals.md`) are reference material, not learning material; the learning focus is `notes/supervised-ml-fundamentals.md`, and VER-3 is closed without an owner citation spot-check.
- 2026-11-07, owner decision: stop trying to run the legacy tools (task ce4 closed with its findings). The owner's account of CellProfiler (GUI to build the object-processing steps from the raw image and the stage-2 maps) and CellProfiler Analyst (GUI to generate a text rule set feeding the CellProfiler stage) is recorded in tasks no9 and hgf and is not yet checked against the `.cppipe` and rules files.
- 2026-11-07, owner decision: close out the rest of Phase 1 before R-3. R-4 (end-to-end data flow and CellProfiler stages) is not pursued beyond the quick read-only pass recorded in `notes/cellprofiler-and-rules.md`; tasks no9 and hgf are closed.

## Unresolved items

Status is `open`, `closed`, `deferred: <reason>`, or `accepted` as a limitation.

| ID | Item | Status |
|---|---|---|
| U-1a | Training annotations and source-image availability: the training images are embedded in each `.ilp` (nine in `mouse.ilp`, eleven in `human.ilp`, all 1040 x 1408, 8-bit). Owner statement 2026-11-07: the original images do not exist; none were found in the repository or on the machine used. Whether the embedded images match the originals therefore cannot be checked. Accepted as a limitation for R-3 | `accepted` |
| U-1b | Independent evaluation ground truth: owner statement 2026-11-07: none exists; none was located in the repository or on the machine used. The classifier's accuracy on new data therefore cannot be measured from existing material. Accepted as a limitation for R-3 | `accepted` |
| U-2 | Legacy tools (ilastik 1.3.x, CellProfiler 3.1.9, old Python and h5py): they were not run. Obstacles recorded 2026-11-07: this machine is arm64 and Rosetta is not installed; the ilastik 1.3.x macOS builds and conda packages are Intel-only, CellProfiler 3.1.9 is not packaged for arm64 and no container runtime is installed (the packaging and build-architecture points come from web search, not from running them); old Python and h5py were not tried. Owner decision: not worth further effort | `accepted` |
| U-3a | `.ilp` contents: inspection is the work of the training task and is static (read-only, no legacy tools) Done 2026-11-07: `notes/inspect_ilp.py` and `notes/training-and-inference.md`. | `closed` |
| U-3b | `.cppipe` and rules files: only a quick read-only pass on `mouse.cppipe` and `mouse_rules.txt` was made (2026-11-07), plus module names for the other pipelines; the outline is in `notes/cellprofiler-and-rules.md`. Settings of the other pipelines and line-level detail are not studied. Accepted as a limitation | `accepted` |
| U-5 | Source versions read: ilastik-meta tags 1.3.2rc2 and 1.3.3post2 (pinned ilastik, lazyflow, volumina commits listed in `notes/ilastik-internals.md`) and VIGRA `Version-1-11-1` as a stand-in. Unknown: the VIGRA version and whether `fastfilters` were inside the binary actually used Accepted 2026-11-07: the bundled build cannot be determined without the original binary, and the legacy tools do not run here (U-2). | `accepted` |
| U-4 | Independent review of the notes: Codex review run 2026-11-05 (8 findings), fixes committed (93a774c), re-review run the same day. The re-review ran `notes/inspect_ilp.py` in a prebuilt virtualenv and independently verified the annotation counts, feature and classifier values and embedded-image shapes; it found 3 smaller points (1 at P2, 2 at P3), fixed in the next commit; a third review pass was declined by the owner Closed 2026-11-07: Codex reviews also ran on the source notes (5 findings) and on the fundamentals notes, pictures and answers (9 and 9 findings), all fixed; the fixes from the last round were not re-reviewed, and the owner reviewed none of it item by item. | `closed` |

## Acceptance

Accepted commit: none
