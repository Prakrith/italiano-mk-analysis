# CellProfiler pipelines and CPA rules: outline

Source: a quick read-only pass on 2026-11-07 over `pipelines/mouse.cppipe` and `pipelines/cpa_rules/mouse_rules.txt`, with settings decoded by `notes/dump_cppipe.py` (`python3 -I notes/dump_cppipe.py pipelines/mouse.cppipe list`, or a comma-separated list of module numbers). Nothing was run. The other pipelines were compared by module names only. Statements are tagged *(file)*, *(owner)* or *(background)*; unknowns are listed at the end.

*(owner)* CellProfiler was used as a GUI to build the processing steps that take the raw image and the stage-2 maps and derive objects. CellProfiler Analyst was used as a GUI to generate a text rule set that feeds the CellProfiler part of the pipeline to improve object classification. The file contents below match this in outline.

## Inputs (`mouse.cppipe` module #3, NamesAndTypes)

*(file)* Five image assignments are matched by metadata. Four are the stage-2 PNGs, selected by a metadata field named `ilastik`, which the Metadata module (#2) extracts from the file name with the expression `..._(?P<ilastik>[0-9]+)\.`, that is the number before the extension in the `_prbstg2_<i>.png` names: 0 is `background`, 1 is `cell_boundary`, 2 is `mk`, 3 is `pplt`, the same order as `LABEL_LIST` and the `_prbstg2_<i>` file suffix in `mk/util/il.py`. The fifth, `phase`, is the original image from a folder named `single_images`. All are grayscale, with "Set intensity range from = Image metadata" and a stored maximum of 255.0; the effective intensity range of the loaded PNGs (which `il.py` writes as 16-bit) was not checked. The setting named `DNA` is the default single-image name; it is not one of the five assignments (assignment method is rules, single-image count 0).

## The mk branch (#5 to #8, #14, #15)

*(file)* In order:
1. `Opening` on `mk` with a disk of radius 3 (#5).
2. `ImageMath` Add (#6): `mk_open` minus `background` minus `pplt` (multipliers 1, -1, -1), clipped to 0 to 1.
3. `Threshold` (#7): global, manual threshold 0.5.
4. `IdentifyPrimaryObjects` (#8): diameter 10 to 500 pixels, clumps split by shape, holes filled.
5. `MeasureObjectSizeShape` (#14) on `mk` and `pplt`, with Zernike features.
6. `FilterObjects` (#15) on `mk`: mode Measurements, keep objects with `AreaShape_Solidity` of at least 0.8. A rules file name is set but this mode does not use it.

So the decision from scores to a mask for `mk` is a fixed 0.5 threshold on a derived map, made here and not in `il.py`.

## The pplt branch (#9 to #13, #16)

*(file)* In order:
1. `ImageMath` Add (#9): `pplt` minus `background` minus `cell_boundary` (multipliers 1, -1, -1).
2. `EnhanceOrSuppressFeatures` (#10): Enhance, line structures, feature size 5.
3. `Closing` (#11): disk of radius 3.
4. `Threshold` (#12): global, manual threshold 0.5.
5. `IdentifyPrimaryObjects` (#13): diameter 10 to 1000 pixels.
6. `FilterObjects` (#16) on `pplt`: mode Rules, rules file `mouse_rules.txt` from the default input folder.

## Rules file (`pipelines/cpa_rules/mouse_rules.txt`)

*(file)* Five lines of the form `IF (<measurement> > <threshold>, [a, -a], [b, -b])`, all on `pplt` shape measurements: `AreaShape_MajorAxisLength`, `AreaShape_MaxFeretDiameter` and Zernike moments 2_2, 4_4 and 7_7. *(background)* This is the rule format of CellProfiler Analyst's classifier, in which each line adds a score to each of two classes and the class with the larger total wins; that was not verified here. Unknown: which class `FilterObjects` keeps (the module has "Class number = 1"), and how these rules were trained or on what data.

## Later modules and exports

*(file)* After the filters, `mouse.cppipe` overlays outlines and saves images, converts objects to images, and measures area occupied, granularity and texture. `ExportToSpreadsheet` writes comma-separated files with prefix `results_`, and two `ExportToDatabase` modules (#30 and #31) write SQLite databases (`results_mk.db` and `results_pplt.db`), at least the first with the option "Create a CellProfiler Analyst properties file" set to Yes. The module list is `#1 Images` to `#31 ExportToDatabase`.

## Other pipelines (module names only)

*(file)* `human.cppipe` has the same module sequence as `mouse.cppipe` (settings not compared). `mouse_nofilter.cppipe` and `human_nofilter.cppipe` have no `FilterObjects` step and fewer measurement modules. `skel.cppipe` works on masked objects with `MeasureObjectSkeleton`. `fluo.cppipe` handles fluorescence images with illumination correction and intensity measurements.

## Unknown

- The settings of the other pipelines beyond their module names, and how `config.ini` selects among them.
- How the rules were produced and which class they keep.
- How the thresholds (0.5) and size limits were chosen.
- Whether results are accurate; no ground truth exists (U-1b in `PROJECT.md`).
