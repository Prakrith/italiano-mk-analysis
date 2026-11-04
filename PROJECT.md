# Project record

Tasks live in Beads, in this repository's `.beads/` directory, and this record is `PROJECT.md` at the repository root. The repository is public, so write both for publication.

## Objective

Phase 1 (now): understand how the legacy supervised-ML segmentation and classification pipeline is trained and how inference runs, from the code and the ilastik project files. The data flow and the CellProfiler stages come after that. Phase 2 (later, separate scope): reimplement it with contemporary techniques that improve segmentation and classification.

## Intended use

Owner's learning and planning. The reimplementation in Phase 2 would analyze phase-contrast TIF time-lapses of megakaryocyte (MK) and proplatelet (pplt) differentiation.

## Requirements

- **R-1.** A written explanation of training and inference in the legacy pipeline: features, labels, classifier, Autocontext stages and training annotations (from the `.ilp` files), and the headless inference call and probability outputs (from `mk/util/il.py`), citing files and lines.
- **R-2.** A written explanation of the supervised-ML fundamentals behind that training and inference, at a level the owner can explain.
- **R-4.** (Lower priority, after R-1 and R-2.) The end-to-end data flow and the CellProfiler and CPA-rules stages, citing the files that define each step.
- **R-3.** A list of the pipeline's limitations and open questions, and candidate modern methods for Phase 2, each marked as a hypothesis until tested.

## Criteria

Status is `open`, `satisfied`, `not satisfied`, or `not applicable` with a reason.

| ID | Type | Traces to | Method | Evidence | Status |
|---|---|---|---|---|---|
| VER-1 | Verification | R-1, R-4 | Each step names the file and line or module that implements it; owner spot-checks against the code | | `open` |
| VER-2 | Verification | R-2 | Claims about the .ilp and rules files come from inspecting those files, not from memory | | `open` |
| VAL-1 | Validation | Intended use | Owner can explain the pipeline from the notes without the code open | | `open` |

## Decisions

- Tasks and this record live in the public code repository, so their text is written to be published; nothing private is recorded in them.

## Unresolved items

Status is `open`, `closed`, `deferred: <reason>`, or `accepted` as a limitation.

| ID | Item | Status |
|---|---|---|
| U-1 | No labeled ground truth has been located; the data location and any manual annotations are unknown | `open` |
| U-2 | Legacy tools (ilastik 1.3.x, CellProfiler 3.1.9, old Python and h5py) may not run on this machine | `open` |
| U-3 | `.ilp` and `.cppipe` contents have not been inspected; descriptions of Autocontext and stage structure come from filenames and code only | `open` |

## Acceptance

Accepted commit: none
