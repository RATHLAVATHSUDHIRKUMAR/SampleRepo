#!/usr/bin/env python
"""Create a compact quantitative and visual audit for an nnU-Net lung fold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import SimpleITK as sitk

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worst", type=int, default=3)
    return parser.parse_args()


def case_id(path: str) -> str:
    name = Path(path).name
    return name[:-7] if name.endswith(".nii.gz") else Path(name).stem


def render_overlay(
    image_path: Path,
    reference_path: Path,
    prediction_path: Path,
    dice: float,
    output_path: Path,
) -> None:
    image = sitk.GetArrayFromImage(sitk.ReadImage(str(image_path))).astype(float)
    reference = sitk.GetArrayFromImage(sitk.ReadImage(str(reference_path))) > 0
    prediction = sitk.GetArrayFromImage(sitk.ReadImage(str(prediction_path))) > 0
    slice_index = int(np.argmax(reference.sum(axis=(1, 2))))

    plane = image[slice_index]
    lo, hi = np.percentile(plane, [1, 99])
    plane = np.clip((plane - lo) / max(hi - lo, 1e-6), 0, 1)
    truth = reference[slice_index]
    pred = prediction[slice_index]
    false_positive = pred & ~truth
    false_negative = truth & ~pred

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), constrained_layout=True)
    for axis in axes:
        axis.imshow(plane, cmap="gray")
        axis.axis("off")
    axes[0].set_title(f"MRI slice {slice_index}")
    axes[1].contour(truth, levels=[0.5], colors=["#00d084"], linewidths=1.2)
    axes[1].contour(pred, levels=[0.5], colors=["#ffcc00"], linewidths=1.2)
    axes[1].set_title("Truth (green) / prediction (yellow)")
    error = np.zeros((*truth.shape, 4), dtype=float)
    error[false_positive] = (1.0, 0.2, 0.2, 0.7)
    error[false_negative] = (0.2, 0.5, 1.0, 0.7)
    axes[2].imshow(error)
    axes[2].set_title("FP (red) / FN (blue)")
    fig.suptitle(f"{case_id(str(prediction_path))} — Dice {dice:.4f}")
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    summary_path = args.validation / "summary.json"
    summary = json.loads(summary_path.read_text())
    rows = []
    for item in summary["metric_per_case"]:
        metric = item["metrics"]["1"]
        rows.append(
            {
                "case_id": case_id(item["prediction_file"]),
                "dice": metric["Dice"],
                "iou": metric["IoU"],
                "false_positive_voxels": metric["FP"],
                "false_negative_voxels": metric["FN"],
                "reference_voxels": metric["n_ref"],
                "predicted_voxels": metric["n_pred"],
                "prediction_file": item["prediction_file"],
                "reference_file": item["reference_file"],
            }
        )

    frame = pd.DataFrame(rows).sort_values("dice").reset_index(drop=True)
    args.output.mkdir(parents=True, exist_ok=True)
    public_columns = [
        "case_id",
        "dice",
        "iou",
        "false_positive_voxels",
        "false_negative_voxels",
        "reference_voxels",
        "predicted_voxels",
    ]
    frame[public_columns].to_csv(args.output / "per_case_metrics.csv", index=False)

    selected = list(range(min(args.worst, len(frame))))
    selected.extend([len(frame) // 2, len(frame) - 1])
    selected = list(dict.fromkeys(selected))
    for index in selected:
        row = frame.iloc[index]
        image_path = args.images / f"{row.case_id}_0000.nii.gz"
        render_overlay(
            image_path,
            Path(row.reference_file),
            Path(row.prediction_file),
            float(row.dice),
            args.output / f"overlay_{row.case_id}.png",
        )

    report = {
        "case_count": int(len(frame)),
        "mean_dice": float(frame.dice.mean()),
        "median_dice": float(frame.dice.median()),
        "minimum_dice": float(frame.dice.min()),
        "maximum_dice": float(frame.dice.max()),
        "cases_below_0_90": int((frame.dice < 0.90).sum()),
        "cases_below_0_85": int((frame.dice < 0.85).sum()),
        "selected_overlays": [frame.iloc[i].case_id for i in selected],
    }
    (args.output / "audit_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print("\nWeakest cases:")
    print(frame[["case_id", "dice", "iou"]].head(args.worst).to_string(index=False))


if __name__ == "__main__":
    main()