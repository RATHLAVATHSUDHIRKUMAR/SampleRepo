#!/usr/bin/env python3
"""Merge nnU-Net lung and lesion predictions into one labeled NIfTI mask."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import SimpleITK as sitk


LOG = logging.getLogger("merge_masks")
INPUT_SUFFIX = "_0000.nii.gz"
MASK_SUFFIX = ".nii.gz"


def same_geometry(reference: sitk.Image, moving: sitk.Image) -> bool:
    """Return whether two images occupy the same sampled physical space."""
    return (
        reference.GetDimension() == moving.GetDimension()
        and reference.GetSize() == moving.GetSize()
        and np.allclose(reference.GetSpacing(), moving.GetSpacing())
        and np.allclose(reference.GetOrigin(), moving.GetOrigin())
        and np.allclose(reference.GetDirection(), moving.GetDirection())
    )


def align_mask(reference: sitk.Image, mask: sitk.Image, name: str) -> sitk.Image:
    """Resample a label image onto the reference grid when geometry differs."""
    if same_geometry(reference, mask):
        return mask

    LOG.warning("Resampling %s to the input-image geometry", name)
    return sitk.Resample(
        mask,
        reference,
        sitk.Transform(),
        sitk.sitkNearestNeighbor,
        0,
        mask.GetPixelID(),
    )


def case_ids(images_dir: Path) -> Iterable[str]:
    for image_path in sorted(images_dir.glob(f"*{INPUT_SUFFIX}")):
        yield image_path.name[: -len(INPUT_SUFFIX)]


def merge_case(
    image_path: Path,
    lung_path: Path,
    lesion_path: Path,
    output_path: Path,
) -> None:
    image = sitk.ReadImage(str(image_path))
    lung = align_mask(image, sitk.ReadImage(str(lung_path)), lung_path.name)
    lesion = align_mask(image, sitk.ReadImage(str(lesion_path)), lesion_path.name)

    lung_array = sitk.GetArrayFromImage(lung) > 0
    lesion_array = sitk.GetArrayFromImage(lesion) > 0

    combined = np.zeros(lung_array.shape, dtype=np.uint8)
    combined[lung_array] = 1
    combined[lung_array & lesion_array] = 2

    combined_image = sitk.GetImageFromArray(combined)
    combined_image.CopyInformation(image)
    for key in image.GetMetaDataKeys():
        combined_image.SetMetaData(key, image.GetMetaData(key))

    sitk.WriteImage(combined_image, str(output_path), useCompression=True)


def existing_directory(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {path}")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Merge binary lung and lesion predictions. Output labels are "
            "0=background, 1=lung, and 2=lesion inside lung."
        )
    )
    parser.add_argument("--images", type=existing_directory, required=True)
    parser.add_argument("--lung-masks", type=existing_directory, required=True)
    parser.add_argument("--lesion-masks", type=existing_directory, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace existing combined masks."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output_dir = args.output.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cases = list(case_ids(args.images))
    if not cases:
        raise SystemExit(f"No *{INPUT_SUFFIX} images found in {args.images}")

    missing: list[Path] = []
    for case_id in cases:
        for path in (
            args.lung_masks / f"{case_id}{MASK_SUFFIX}",
            args.lesion_masks / f"{case_id}{MASK_SUFFIX}",
        ):
            if not path.is_file():
                missing.append(path)
    if missing:
        formatted = "\n".join(f"  - {path}" for path in missing)
        raise SystemExit(f"Missing prediction masks:\n{formatted}")

    for case_id in cases:
        output_path = output_dir / f"{case_id}{MASK_SUFFIX}"
        if output_path.exists() and not args.overwrite:
            raise SystemExit(
                f"Output exists: {output_path}. Use --overwrite to replace outputs."
            )
        LOG.info("Merging %s", case_id)
        merge_case(
            args.images / f"{case_id}{INPUT_SUFFIX}",
            args.lung_masks / f"{case_id}{MASK_SUFFIX}",
            args.lesion_masks / f"{case_id}{MASK_SUFFIX}",
            output_path,
        )

    LOG.info("Wrote %d combined mask(s) to %s", len(cases), output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

