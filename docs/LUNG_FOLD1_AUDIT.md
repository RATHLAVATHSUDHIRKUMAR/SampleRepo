# Lung Fold 1 Validation Audit

Fold 1 completed 500 training epochs using the `3d_safe96` configuration with
81 training scans and 22 mouse-grouped validation scans. No mouse appears in
both partitions.

## Checkpoint comparison

| Metric | Final checkpoint | Best checkpoint |
|---|---:|---:|
| Mean Dice | 0.8300 | **0.8414** |
| Median Dice | 0.9155 | **0.9338** |
| Minimum Dice | 0.2101 | **0.2325** |
| Maximum Dice | **0.9825** | 0.9803 |
| Cases below 0.85 | 6 | **5** |
| Cases below 0.90 | **7** | 8 |

The saved best checkpoint was selected for downstream out-of-fold anatomical
guidance because it achieved the higher mean and median Dice. Its 22 soft
probability maps were exported in nnU-Net `.npz` format.

The paired comparison is mixed: the best checkpoint improved 8 cases and
reduced 14 relative to the final checkpoint. The mean Dice improvement of
0.0114 was strongly influenced by `deepmeta_099_Plc_c2_05Corr_1`, which improved
by 0.2551. The largest reduction was 0.0340. The checkpoint choice therefore
reflects aggregate validation performance, not a uniform per-scan improvement.

## Difficult cases

The three weakest selected-best predictions were:

| Case | Dice |
|---|---:|
| `deepmeta_090_m2Pc_c3_06Corr_1` | 0.2325 |
| `deepmeta_095_m2PRc_c3_07Corr_1` | 0.3337 |
| `deepmeta_088_m2P_c3_07Corr_1` | 0.5358 |

These outliers must remain visible in downstream uncertainty analysis. A high
fold-level mean alone is not sufficient evidence that the anatomical guidance
is reliable for every scan.

## Reproducible artifacts

- `outputs/deepmeta/lung_fold1_final_audit/`: sanitized final-checkpoint metrics
  and representative overlays.
- `outputs/deepmeta/lung_fold1_best_audit/`: sanitized selected-best metrics and
  representative overlays.
- `outputs/deepmeta/lung_fold1_checkpoint_comparison.csv`: paired per-case
  checkpoint differences.
- The large checkpoints, masks, and probability arrays remain local/Zenodo
  artifacts and are intentionally excluded from GitHub.

