#!/usr/bin/env python3
"""Build a two-channel lesion dataset from MRI and out-of-fold lung probabilities."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import SimpleITK as sitk


def probability_file(results: Path, fold: int, case_id: str) -> Path:
    candidates = list((results / f"fold_{fold}").rglob(f"{case_id}.npz"))
    candidates = [p for p in candidates if "validation" in {x.lower() for x in p.parts}]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected one validation probability for {case_id} in fold {fold}; "
            f"found {len(candidates)}: {candidates}"
        )
    return candidates[0]


def foreground_probability(path: Path) -> np.ndarray:
    with np.load(path) as archive:
        if "probabilities" not in archive:
            raise KeyError(f"{path} has no 'probabilities' array")
        probabilities = archive["probabilities"]
    if probabilities.ndim != 4 or probabilities.shape[0] < 2:
        raise ValueError(f"Unexpected probability shape {probabilities.shape} in {path}")
    return probabilities[1].astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=Path, default=Path("data/processed/deepmeta"))
    parser.add_argument("--lung-results", type=Path, required=True)
    parser.add_argument("--dataset-id", type=int, default=202)
    args = parser.parse_args()

    root = args.processed.resolve()
    staging = root / "lesion_guidance_staging"
    manifest = pd.read_csv(root / "deepmeta_manifest.csv")
    eligible = manifest[manifest["lesion_training_eligible"]].copy()
    folds = json.loads((root / "splits_final.json").read_text())

    case_to_fold: dict[str, int] = {}
    for fold, split in enumerate(folds):
        for case_id in split["val"]:
            if case_id in case_to_fold:
                raise RuntimeError(f"Case occurs in multiple validation folds: {case_id}")
            case_to_fold[case_id] = fold

    dataset_name = f"Dataset{args.dataset_id:03d}_DeepMetaAnatomyGuidedLesion"
    output = root / "nnUNet_raw" / dataset_name
    images = output / "imagesTr"
    labels = output / "labelsTr"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)

    audit = []
    for row in eligible.itertuples(index=False):
        case_id = row.case_id
        if case_id not in case_to_fold:
            raise RuntimeError(f"Eligible lesion case is absent from lung validation folds: {case_id}")
        fold = case_to_fold[case_id]
        reference_path = staging / "images" / f"{case_id}_0000.nii.gz"
        label_path = staging / "labels" / f"{case_id}.nii.gz"
        source_probability = probability_file(args.lung_results, fold, case_id)
        reference = sitk.ReadImage(str(reference_path))
        probability = foreground_probability(source_probability)
        if probability.shape != tuple(reversed(reference.GetSize())):
            raise ValueError(
                f"Shape mismatch for {case_id}: probability {probability.shape}, "
                f"MRI {tuple(reversed(reference.GetSize()))}"
            )
        probability_image = sitk.GetImageFromArray(probability)
        probability_image.CopyInformation(reference)
        shutil.copy2(reference_path, images / f"{case_id}_0000.nii.gz")
        sitk.WriteImage(probability_image, str(images / f"{case_id}_0001.nii.gz"), True)
        shutil.copy2(label_path, labels / f"{case_id}.nii.gz")
        audit.append({"case_id": case_id, "lung_oof_fold": fold})

    dataset_json = {
        "channel_names": {"0": "MRI", "1": "OOF_lung_probability"},
        "labels": {"background": 0, "lesion": 1},
        "numTraining": len(audit),
        "file_ending": ".nii.gz",
    }
    (output / "dataset.json").write_text(json.dumps(dataset_json, indent=2) + "\n")
    shutil.copy2(root / "lesion_splits_final.json", output / "splits_final.json")
    pd.DataFrame(audit).to_csv(output / "oof_probability_audit.csv", index=False)
    print(json.dumps({"dataset": str(output), "cases": len(audit)}, indent=2))


if __name__ == "__main__":
    main()
