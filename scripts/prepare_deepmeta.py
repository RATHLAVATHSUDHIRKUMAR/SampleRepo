#!/usr/bin/env python3
"""Convert the public DeepMeta TIFF dataset into leakage-safe nnU-Net datasets.

The Zenodo archive stores each MRI as one 128-slice TIFF stack while lung and
metastasis annotations are individual TIFF slices named by ``case_id * 128 +
slice_index``. This utility reconstructs the 3D masks, writes physical-space
NIfTI images, and creates mouse-grouped cross-validation splits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import SimpleITK as sitk
import tifffile
from sklearn.model_selection import StratifiedGroupKFold


EXPECTED_MD5 = "cd0b81da901d808f50886206da6dc253"
SPACING_XYZ_MM = (20.0 / 128.0, 20.0 / 128.0, 25.0 / 128.0)
STACK_DEPTH = 128


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_mouse_id(name: str) -> str:
    """Derive a stable biological mouse ID from the published scan name."""
    stem = Path(name).stem
    day_match = re.match(r"(.+?)_day\d+", stem, flags=re.IGNORECASE)
    if day_match:
        return day_match.group(1)

    cage_match = re.match(r"(.+?_c\d+)(?:_|$)", stem, flags=re.IGNORECASE)
    if cage_match:
        return cage_match.group(1)

    juvenile_match = re.match(r"(.+?)_j\d+", stem, flags=re.IGNORECASE)
    if juvenile_match:
        return juvenile_match.group(1)

    # Fallback strips acquisition/reconstruction suffixes while retaining the
    # biological identifier. It is included in the manifest for manual audit.
    return re.split(r"_(?:\d+Corr|\d+scan|Corr)", stem, maxsplit=1)[0]


def timepoint_days(name: str) -> int | None:
    match = re.search(r"_(?:day|j)(\d+)", Path(name).stem, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def safe_case_id(dataset_id: int, name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", Path(name).stem).strip("_")
    return f"deepmeta_{dataset_id:03d}_{normalized}"


def indexed_slices(folder: Path) -> dict[int, Path]:
    result: dict[int, Path] = {}
    for path in folder.glob("*.tif"):
        if path.stem.isdigit():
            result[int(path.stem)] = path
    return result


def reconstruct_mask(
    case_number: int,
    slice_paths: dict[int, Path],
    shape: tuple[int, int, int],
) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    start = case_number * STACK_DEPTH
    for slice_index in range(STACK_DEPTH):
        path = slice_paths.get(start + slice_index)
        if path is not None:
            plane = tifffile.imread(path)
            if plane.shape != shape[1:]:
                raise ValueError(
                    f"Unexpected label shape {plane.shape} for {path}; "
                    f"expected {shape[1:]}"
                )
            mask[slice_index] = plane > 0
    return mask


def write_nifti(array: np.ndarray, output: Path, *, is_label: bool) -> None:
    image = sitk.GetImageFromArray(array.astype(np.uint8 if is_label else np.float32))
    image.SetSpacing(SPACING_XYZ_MM)
    image.SetMetaData("DeepMeta_source", "Zenodo 10.5281/zenodo.6805921")
    image.SetMetaData("DeepMeta_sequence", "self-gated 3D bSSFP")
    output.parent.mkdir(parents=True, exist_ok=True)
    sitk.WriteImage(image, str(output), useCompression=True)


def grouped_splits(manifest: pd.DataFrame, folds: int, seed: int) -> list[dict]:
    groups = manifest["mouse_id"].astype(str).to_numpy()
    # Joint stratification preserves lesion status and mutation group as far as
    # possible while GroupKFold guarantees that a mouse never crosses folds.
    strata = (
        manifest["mutation"].fillna("unknown").astype(str)
        + "__"
        + manifest["has_metastasis"].astype(int).astype(str)
    ).to_numpy()
    dummy = np.zeros(len(manifest), dtype=np.uint8)
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    splits: list[dict] = []
    for train_indices, val_indices in splitter.split(dummy, strata, groups):
        train = manifest.iloc[train_indices]["case_id"].sort_values().tolist()
        val = manifest.iloc[val_indices]["case_id"].sort_values().tolist()
        train_groups = set(manifest.iloc[train_indices]["mouse_id"])
        val_groups = set(manifest.iloc[val_indices]["mouse_id"])
        overlap = train_groups & val_groups
        if overlap:
            raise RuntimeError(f"Mouse leakage in generated split: {sorted(overlap)}")
        splits.append({"train": train, "val": val})
    return splits


def restrict_splits(splits: list[dict], eligible_case_ids: set[str]) -> list[dict]:
    return [
        {
            "train": [case for case in split["train"] if case in eligible_case_ids],
            "val": [case for case in split["val"] if case in eligible_case_ids],
        }
        for split in splits
    ]


def dataset_json(channel_names: dict[str, str], labels: dict[str, int], count: int) -> dict:
    return {
        "channel_names": channel_names,
        "labels": labels,
        "numTraining": count,
        "file_ending": ".nii.gz",
        "overwrite_image_reader_writer": "SimpleITKIO",
    }


def convert(source: Path, output: Path, folds: int, seed: int) -> None:
    metadata = pd.read_csv(source / "mouse_ID.csv")
    raw_by_id = {
        int(path.name.split("_", 1)[0]): path
        for path in (source / "Raw_data").glob("*.tif")
    }
    lung_slices = indexed_slices(source / "Lungs" / "Labels")
    lesion_slices = indexed_slices(source / "Metastases" / "Labels")
    lung_cases = {index // STACK_DEPTH for index in lung_slices}
    lesion_cases = {index // STACK_DEPTH for index in lesion_slices}

    eligible = sorted(set(raw_by_id) & lung_cases)
    if not eligible:
        raise RuntimeError("No raw cases with lung annotations were found")

    lung_root = output / "nnUNet_raw" / "Dataset201_DeepMetaLung"
    lesion_stage = output / "lesion_guidance_staging"
    records: list[dict] = []

    for case_number in eligible:
        row = metadata.loc[metadata["Id"] == case_number]
        if len(row) != 1:
            raise ValueError(f"Expected one metadata row for case {case_number}")
        row = row.iloc[0]
        raw_path = raw_by_id[case_number]
        volume = tifffile.imread(raw_path)
        if volume.shape != (STACK_DEPTH, 128, 128):
            raise ValueError(f"Unexpected image shape {volume.shape} for {raw_path}")

        lung = reconstruct_mask(case_number, lung_slices, volume.shape)
        lesion = reconstruct_mask(case_number, lesion_slices, volume.shape)
        has_metastasis = str(row["Saine/Metas"]).strip().lower() == "m"
        lesion_annotation_available = case_number in lesion_cases
        if lesion_annotation_available and not has_metastasis:
            raise ValueError(
                f"Case {case_number} metastasis metadata/annotation mismatch: "
                f"metadata={has_metastasis}, labels={lesion_annotation_available}"
            )
        if np.any(lesion & ~lung):
            # Preserve the expert lesion annotation and include it in the lung
            # region so that anatomy guidance cannot contradict ground truth.
            lung |= lesion

        case_id = safe_case_id(case_number, str(row["Name"]))
        write_nifti(volume, lung_root / "imagesTr" / f"{case_id}_0000.nii.gz", is_label=False)
        write_nifti(lung, lung_root / "labelsTr" / f"{case_id}.nii.gz", is_label=True)

        # A healthy scan is a valid negative. A metastatic scan is eligible only
        # when its lesion annotation was actually released. Metastatic scans
        # without masks must never be silently converted into negative examples.
        lesion_training_eligible = (not has_metastasis) or lesion_annotation_available
        if lesion_training_eligible:
            # This becomes a two-channel nnU-Net dataset only after out-of-fold
            # P(lung) maps are generated. Keep MRI and labels staged for now.
            write_nifti(volume, lesion_stage / "images" / f"{case_id}_0000.nii.gz", is_label=False)
            write_nifti(lesion, lesion_stage / "labels" / f"{case_id}.nii.gz", is_label=True)

        records.append(
            {
                "case_id": case_id,
                "source_id": case_number,
                "source_name": row["Name"],
                "mouse_id": canonical_mouse_id(str(row["Name"])),
                "timepoint_days": timepoint_days(str(row["Name"])),
                "status": str(row["Saine/Metas"]),
                "has_metastasis": has_metastasis,
                "lesion_annotation_available": lesion_annotation_available,
                "lesion_training_eligible": lesion_training_eligible,
                "mutation": None if pd.isna(row["Mutation"]) else str(row["Mutation"]),
                "notes": None if pd.isna(row["info"]) else str(row["info"]),
                "lung_voxels": int(lung.sum()),
                "lesion_voxels": int(lesion.sum()),
                "voxel_volume_mm3": float(np.prod(SPACING_XYZ_MM)),
            }
        )

    manifest = pd.DataFrame.from_records(records).sort_values("source_id")
    output.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(output / "deepmeta_manifest.csv", index=False)
    splits = grouped_splits(manifest, folds=folds, seed=seed)
    (output / "splits_final.json").write_text(json.dumps(splits, indent=2) + "\n")
    lesion_case_ids = set(
        manifest.loc[manifest["lesion_training_eligible"], "case_id"].astype(str)
    )
    lesion_splits = restrict_splits(splits, lesion_case_ids)
    (output / "lesion_splits_final.json").write_text(
        json.dumps(lesion_splits, indent=2) + "\n"
    )
    (lung_root / "dataset.json").write_text(
        json.dumps(dataset_json({"0": "SG-bSSFP MRI"}, {"background": 0, "lung": 1}, len(manifest)), indent=2)
        + "\n"
    )
    (lesion_stage / "dataset_template.json").write_text(
        json.dumps(
            dataset_json(
                {"0": "SG-bSSFP MRI", "1": "out-of-fold lung probability"},
                {"background": 0, "metastasis": 1},
                len(lesion_case_ids),
            ),
            indent=2,
        )
        + "\n"
    )

    summary = {
        "eligible_cases": len(manifest),
        "unique_mice": int(manifest["mouse_id"].nunique()),
        "metastasis_positive_cases": int(manifest["has_metastasis"].sum()),
        "lesion_annotated_positive_cases": int(
            manifest["lesion_annotation_available"].sum()
        ),
        "metastatic_cases_excluded_from_lesion_training": int(
            (manifest["has_metastasis"] & ~manifest["lesion_annotation_available"]).sum()
        ),
        "healthy_negative_cases": int((~manifest["has_metastasis"]).sum()),
        "lesion_training_cases": len(lesion_case_ids),
        "longitudinal_cases_with_known_days": int(manifest["timepoint_days"].notna().sum()),
        "spacing_xyz_mm": SPACING_XYZ_MM,
        "voxel_volume_mm3": float(np.prod(SPACING_XYZ_MM)),
        "folds": folds,
        "seed": seed,
    }
    (output / "conversion_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Optional Zenodo ZIP to verify")
    parser.add_argument("--source", type=Path, required=True, help="Extracted deepmeta_dataset directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.archive:
        actual = md5(args.archive)
        if actual != EXPECTED_MD5:
            raise SystemExit(f"Archive MD5 mismatch: expected {EXPECTED_MD5}, got {actual}")
        print(f"Archive MD5 verified: {actual}")
    convert(args.source.resolve(), args.output.resolve(), args.folds, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
