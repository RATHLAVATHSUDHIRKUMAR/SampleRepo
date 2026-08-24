#!/usr/bin/env python3
"""Export small, non-image DeepMeta artifacts intended for GitHub.

Raw images, masks, checkpoints, preprocessed arrays, probabilities, and local
paths are deliberately excluded. The export can be regenerated after dataset
conversion or split changes.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd


PUBLIC_MANIFEST_COLUMNS = [
    "case_id",
    "source_id",
    "source_name",
    "mouse_id",
    "timepoint_days",
    "status",
    "has_metastasis",
    "lesion_annotation_available",
    "lesion_training_eligible",
    "mutation",
    "lung_voxels",
    "lesion_voxels",
    "voxel_volume_mm3",
]


def copy_json(source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text())
    destination.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=Path, default=Path("data/processed/deepmeta"))
    parser.add_argument("--output", type=Path, default=Path("metadata/deepmeta"))
    args = parser.parse_args()

    source = args.processed.resolve()
    output = args.output.resolve()
    configs = output / "configs"
    output.mkdir(parents=True, exist_ok=True)
    configs.mkdir(parents=True, exist_ok=True)

    for filename in (
        "conversion_summary.json",
        "splits_final.json",
        "lesion_splits_final.json",
    ):
        copy_json(source / filename, output / filename)

    manifest = pd.read_csv(source / "deepmeta_manifest.csv")
    missing = sorted(set(PUBLIC_MANIFEST_COLUMNS) - set(manifest.columns))
    if missing:
        raise RuntimeError(f"Manifest is missing required public columns: {missing}")
    manifest[PUBLIC_MANIFEST_COLUMNS].to_csv(output / "case_manifest.csv", index=False)

    lung_preprocessed = source / "nnUNet_preprocessed" / "Dataset201_DeepMetaLung"
    for filename in ("dataset.json", "dataset_fingerprint.json", "nnUNetPlans.json"):
        copy_json(lung_preprocessed / filename, configs / f"lung_{filename}")

    lesion_template = source / "lesion_guidance_staging" / "dataset_template.json"
    copy_json(lesion_template, configs / "lesion_dataset_template.json")

    # This file is static documentation maintained in the repository, not a
    # generated artifact, so do not overwrite it during repeated exports.
    readme = output / "README.md"
    if not readme.exists():
        shutil.copy2(Path(__file__).with_name("public_metadata_README.md"), readme)

    print(f"Exported public metadata for {len(manifest)} cases to {output}")


if __name__ == "__main__":
    main()
