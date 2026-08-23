#!/usr/bin/env python3
"""Quantify released DeepMeta lesion masks and conservative longitudinal trends.

Only cases with released lesion ground truth (or confirmed healthy controls) are
measured. Metastatic scans lacking lesion masks remain missing, never zero.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cc3d
import numpy as np
import pandas as pd
import SimpleITK as sitk
from scipy.stats import mannwhitneyu


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed", type=Path, default=Path("data/processed/deepmeta"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.processed.resolve()
    output = (args.output or root / "longitudinal").resolve()
    output.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(root / "deepmeta_manifest.csv")
    measurements = []
    component_rows = []
    for row in manifest.itertuples(index=False):
        if not row.lesion_training_eligible:
            continue
        label_path = root / "lesion_guidance_staging" / "labels" / f"{row.case_id}.nii.gz"
        image = sitk.ReadImage(str(label_path))
        mask = sitk.GetArrayFromImage(image).astype(bool)
        components = cc3d.connected_components(mask, connectivity=26)
        stats = cc3d.statistics(components)
        voxel_volume = float(np.prod(image.GetSpacing()))
        lesion_voxels = int(mask.sum())
        measurements.append(
            {
                "case_id": row.case_id,
                "mouse_id": row.mouse_id,
                "timepoint_days": row.timepoint_days,
                "mutation": row.mutation,
                "status": row.status,
                "lesion_count": int(components.max()),
                "lesion_voxels": lesion_voxels,
                "lesion_volume_mm3": lesion_voxels * voxel_volume,
            }
        )
        for label in range(1, int(components.max()) + 1):
            centroid_zyx = stats["centroids"][label]
            component_rows.append(
                {
                    "case_id": row.case_id,
                    "mouse_id": row.mouse_id,
                    "timepoint_days": row.timepoint_days,
                    "component": label,
                    "volume_mm3": int(stats["voxel_counts"][label]) * voxel_volume,
                    "centroid_z": centroid_zyx[0],
                    "centroid_y": centroid_zyx[1],
                    "centroid_x": centroid_zyx[2],
                }
            )

    cases = pd.DataFrame(measurements).sort_values(["mouse_id", "timepoint_days"], na_position="last")
    cases.to_csv(output / "case_measurements.csv", index=False)
    pd.DataFrame(component_rows).to_csv(output / "lesion_components.csv", index=False)

    trajectories = []
    timed = cases.dropna(subset=["timepoint_days"])
    for mouse_id, group in timed.groupby("mouse_id"):
        group = group.sort_values("timepoint_days")
        if len(group) < 2:
            continue
        first, last = group.iloc[0], group.iloc[-1]
        elapsed = float(last.timepoint_days - first.timepoint_days)
        trajectories.append(
            {
                "mouse_id": mouse_id,
                "mutation": first.mutation,
                "n_observed_timepoints": len(group),
                "first_day": first.timepoint_days,
                "last_day": last.timepoint_days,
                "first_volume_mm3": first.lesion_volume_mm3,
                "last_volume_mm3": last.lesion_volume_mm3,
                "absolute_change_mm3": last.lesion_volume_mm3 - first.lesion_volume_mm3,
                "change_mm3_per_day": (
                    (last.lesion_volume_mm3 - first.lesion_volume_mm3) / elapsed
                    if elapsed > 0 else np.nan
                ),
            }
        )
    trajectory_df = pd.DataFrame(trajectories)
    trajectory_df.to_csv(output / "mouse_trajectories.csv", index=False)

    # Descriptive/exploratory only: annotation availability and cohort design
    # make this unsuitable for a radiogenomic or causal biological claim.
    phenotype = []
    if not trajectory_df.empty:
        for mutation, group in trajectory_df.groupby("mutation"):
            phenotype.append(
                {
                    "mutation": mutation,
                    "n_mice": len(group),
                    "median_change_mm3_per_day": group.change_mm3_per_day.median(),
                    "mean_change_mm3_per_day": group.change_mm3_per_day.mean(),
                }
            )
    phenotype_df = pd.DataFrame(phenotype)
    if set(trajectory_df.get("mutation", [])) >= {"LacZ", "iL34c"}:
        a = trajectory_df.loc[trajectory_df.mutation == "LacZ", "change_mm3_per_day"].dropna()
        b = trajectory_df.loc[trajectory_df.mutation == "iL34c", "change_mm3_per_day"].dropna()
        if len(a) and len(b):
            test = mannwhitneyu(a, b, alternative="two-sided")
            phenotype_df["exploratory_mannwhitney_p"] = np.nan
            phenotype_df.loc[0, "exploratory_mannwhitney_p"] = test.pvalue
    phenotype_df.to_csv(output / "preliminary_il34_phenotype.csv", index=False)
    print(f"Wrote {len(cases)} cases and {len(trajectory_df)} mouse trajectories to {output}")


if __name__ == "__main__":
    main()
