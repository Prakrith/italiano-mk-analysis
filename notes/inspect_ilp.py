"""Read-only inspection of ilastik .ilp (HDF5) project files.

Reproduces the facts in training-and-inference.md. Needs h5py and numpy
(for example in a throwaway virtualenv). Opens files with mode "r" only and
never unpickles stored objects (the classifier factory is printed as raw bytes).

Usage: python3 -I inspect_ilp.py ilps/mouse.ilp [ilps/human.ilp ...]
"""
import hashlib
import os
import sys

import h5py
import numpy as np

STAGES = (("stage 1", "FeatureSelections", "PixelClassification"),
          ("stage 2", "FeatureSelections01", "PixelClassification01"))


def text(x):
    return x.decode("utf-8") if isinstance(x, bytes) else x


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def label_counts(f, stage_group):
    """Labeled pixels per class, per label set (one per input lane)."""
    names = [text(n) for n in f[stage_group]["LabelNames"][()]]
    sets = f[stage_group]["LabelSets"]
    rows = {}
    for name in sorted(sets):
        c = np.zeros(len(names), int)
        blocks = 0
        for b in sets[name]:
            a = sets[name][b][()]
            blocks += 1
            c += np.bincount(a.ravel(), minlength=len(names) + 1)[1:len(names) + 1]
        rows[name] = (blocks, c)
    return names, rows


def report(path):
    f = h5py.File(path, "r")
    print("=" * 70)
    print("file", os.path.basename(path), "bytes", os.path.getsize(path), "sha256", sha256(path))
    for k in ("workflowName", "ilastikVersion", "time"):
        print(" ", k, text(f[k][()]))
    print("  currentApplet", int(f["currentApplet"][()]))
    pe = f["Prediction Export"]
    print("  Prediction Export:", {k: text(pe[k][()]) for k in pe})

    for label, fs, pc in STAGES:
        print("\n--", label, f"({fs}, {pc})")
        sel = f[fs]
        print("  scales", sel["Scales"][()].tolist(), "ComputeIn2d", sel["ComputeIn2d"][()].tolist())
        for fid, row in zip(sel["FeatureIds"][()], sel["SelectionMatrix"][()]):
            print("   ", text(fid), row.astype(int).tolist())
        print("  selected pairs", int(sel["SelectionMatrix"][()].sum()))
        names, rows = label_counts(f, pc)
        print("  LabelNames", names, "known_labels", f[pc]["ClassifierForests/known_labels"][()].tolist())
        total = np.zeros(len(names), int)
        for name, (blocks, c) in rows.items():
            lane = int(name[6:])
            nick = text(f["Input Data/infos"][f"lane{lane:04d}/Raw Data/nickname"][()])
            print(f"  {name} {nick:28s} blocks={blocks:3d} per-class={c.tolist()} total={int(c.sum())}")
            total += c
        print("  TOTAL per-class", dict(zip(names, total.tolist())), "sum", int(total.sum()))
        cf = f[pc]["ClassifierForests"]
        print("  pickled_type", text(cf["pickled_type"][()]).replace("\n", "\\n"))
        print("  ClassifierFactory (raw bytes)", f[pc]["ClassifierFactory"][()])
        print("  feature_names", len(cf["feature_names"]), "first", text(cf["feature_names"][0]),
              "last", text(cf["feature_names"][-1]))
        for forest in sorted(k for k in cf if k.startswith("Forest")):
            o = cf[forest]
            opt = {n: o["_options"][n][()].tolist() for n in o["_options"]}
            ext = {n: o["_ext_param"][n][()].tolist() for n in o["_ext_param"]}
            trees = sum(1 for t in o if t.startswith("Tree_"))
            print(f"  {forest} trees={trees} options={opt}")
            print(f"    ext_param={ext}")

    print("\n-- Input Data lanes (file path directories omitted)")
    inf = f["Input Data/infos"]
    local = f["Input Data/local_data"]
    for lane in sorted(inf):
        r = inf[lane]["Raw Data"]
        ds = text(r["datasetId"][()])
        print(f"  {lane} nickname={text(r['nickname'][()])} file={os.path.basename(text(r['filePath'][()]))} "
              f"location={text(r['location'][()])} shape={r['shape'][()].tolist()} dtype={text(r['dtype'][()])} "
              f"embedded={ds in local} prediction_mask_keys={list(inf[lane]['Prediction Mask'].keys())}")
    print("  local_data datasets", len(local))
    return f


def compare(a, b, na, nb):
    print("=" * 70)
    print("comparison", na, "vs", nb)
    for _, fs, pc in STAGES:
        for k in ("SelectionMatrix", "Scales", "FeatureIds", "ComputeIn2d"):
            print(f"  {fs}/{k} equal:", np.array_equal(a[fs][k][()], b[fs][k][()]))
        for k in ("LabelNames", "LabelColors", "PmapColors"):
            print(f"  {pc}/{k} equal:", np.array_equal(a[pc][k][()], b[pc][k][()]))


if __name__ == "__main__":
    paths = sys.argv[1:]
    if not paths:
        sys.exit(__doc__)
    files = [report(p) for p in paths]
    for i in range(1, len(files)):
        compare(files[0], files[i], os.path.basename(paths[0]), os.path.basename(paths[i]))
