# Project record

Tasks live in Beads, in this repository's `.beads/` directory, and this record is `PROJECT.md` at the repository root. The repository is public, so write both for publication.

## Objective

Phase 1 (now): understand how the legacy supervised-ML segmentation and classification pipeline is trained and how inference runs, from the code and the ilastik project files. The data flow and the CellProfiler stages come after that. Phase 2 (later, separate scope): reimplement it with contemporary techniques that improve segmentation and classification.

## Intended use

Owner's learning and planning. The reimplementation in Phase 2 would analyze phase-contrast TIF time-lapses of megakaryocyte (MK) and proplatelet (pplt) differentiation.

## Requirements

- **R-1.** A written explanation of training and inference in the legacy pipeline, covering both `ilps/mouse.ilp` and `ilps/human.ilp`: features and scales, labels, classifier, Autocontext stages and training annotations (from the `.ilp` files), and the headless inference call and probability outputs (from `mk/util/il.py`), citing files and lines. "Annotation counts" means labeled pixels per class, per image and per stage. Image references stored in a file are kept separate from images actually available.
- **R-2.** A written explanation of the supervised-ML fundamentals behind that training and inference, at a level the owner can explain. Coverage list: training examples and targets; features; fit versus inference; probabilities versus final decisions; Autocontext; generalization.
- **R-4.** (Lower priority, after R-1 and R-2.) The end-to-end data flow and the CellProfiler and CPA-rules stages, citing the files that define each step.
- **R-3.** (Deferred until training and inference are understood.) A list of the pipeline's limitations and open questions, and candidate modern methods for Phase 2. Observed facts, open questions and hypotheses are kept in separate lists; every candidate method is a hypothesis until tested.

## Criteria

Status is `open`, `satisfied`, `not satisfied`, or `not applicable` with a reason.

| ID | Type | Traces to | Method | Evidence | Status |
|---|---|---|---|---|---|
| VER-1 | Verification | R-1, R-4 | Every R-1 topic is covered for both `mouse.ilp` and `human.ilp`. Information the files do not show is recorded as unknown, never inferred from ilastik defaults. HDF5 evidence cites group, dataset or attribute paths; code evidence cites file and line. The `.ilp` label order is reconciled with `LABEL_LIST` in `mk/util/il.py`. R-4 steps name the file and line or module that implements them. Owner spot-checks against the files | Partial: `notes/training-and-inference.md` covers the R-1 training and inference topics for both files; R-4 and the owner spot-check are not done | `open` |
| VER-2 | Verification | R-2 | The R-2 coverage list is checked item by item against the notes; claims about the `.ilp` and rules files come from inspecting those files, not from memory | Drafted: `notes/supervised-ml-fundamentals.md` with an R-2 coverage table; not yet checked item by item, and not independently reviewed | `open` |
| VAL-1 | Validation | Intended use | Teach-back: the owner explains the R-2 concepts and the pipeline from the notes without the code open | | `open` |

## Decisions

- Tasks and this record live in the public code repository, so their text is written to be published; nothing private is recorded in them.
- Static inspection of the `.ilp` and `.cppipe` files must not depend on the legacy tools running.
- Missing information is recorded as unknown, not inferred from ilastik defaults.
- Candidate modern methods (R-3) wait until training and inference are understood.
- Further work focuses on `mouse.ilp`. `human.ilp` is already covered in the notes; it is an interchangeable project file made for human-megakaryocyte images (owner statement), so it gets no further study.

## Unresolved items

Status is `open`, `closed`, `deferred: <reason>`, or `accepted` as a limitation.

| ID | Item | Status |
|---|---|---|
| U-1a | Training annotations and source-image availability: which images the annotations refer to, and whether those images are available | `open` |
| U-1b | Independent evaluation ground truth: no labeled ground truth separate from the training annotations has been located; its location and any manual annotations are unknown | `open` |
| U-2 | Legacy tools (ilastik 1.3.x, CellProfiler 3.1.9, old Python and h5py) may not run on this machine | `open` |
| U-3a | `.ilp` contents: inspection is the work of the training task and is static (read-only, no legacy tools) | `open` |
| U-3b | `.cppipe` contents have not been inspected; descriptions of the CellProfiler stages come from filenames and code only (later task) | `open` |
| U-4 | Independent review of the notes: Codex review run 2026-11-05 (8 findings), fixes committed (93a774c), re-review run the same day. The re-review ran `notes/inspect_ilp.py` in a prebuilt virtualenv and independently verified the annotation counts, feature and classifier values and embedded-image shapes; it found 3 smaller points (1 at P2, 2 at P3), fixed in the next commit; a third review pass was declined by the owner | `open` |

## Acceptance

Accepted commit: none
