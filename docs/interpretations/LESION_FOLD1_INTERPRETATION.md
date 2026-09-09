# Anatomy-Guided Lesion Fold 1 Interpretation

Status date: 2026-09-08

Fold 1 used 71 training cases and 21 mouse-grouped validation cases. Both input
channels followed the fixed baseline protocol: T2 MRI and an out-of-fold lung
probability map.

## Checkpoint comparison

| Measurement | Final checkpoint | Saved-best checkpoint |
|---|---:|---:|
| Mean foreground Dice | 0.0000 | 0.1091 |
| Lesion-positive cases | 10 | 10 |
| Positive cases detected | 0 | 9 |
| Lesion-negative cases | 11 | 11 |
| Negative cases with false positives | 0 | 11 |
| Mean Dice among positive cases | 0.0000 | 0.2291 |

The final checkpoint collapsed to an all-background solution and missed every
positive case. The saved-best checkpoint retained lesion sensitivity and was
therefore selected for the Fold 1 baseline, but it generated foreground in
every lesion-negative validation scan. Its 21 masks and 21 soft probability
maps were preserved for out-of-fold analysis.

## Interpretation

Fold 1 is a weak baseline rather than a successful final model. The difference
between checkpoints demonstrates instability under severe foreground sparsity.
The selected checkpoint is useful for unbiased cross-fold error analysis, but
its predictions are not suitable for biological conclusions or treatment-
response modelling without correction and external validation.

Corrective experiments should be defined once and applied to every fold. They
should evaluate stronger lesion-positive patch sampling, explicit handling of
lesion-negative scans, threshold calibration, and detection-aware metrics in
addition to voxel Dice.

