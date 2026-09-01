# Anatomy-Guided Lesion Fold 0 Training Status

Status date: 2026-09-01

Fold 0 is the first full training run for the two-channel anatomy-guided lesion
model. The inputs are T2 MRI and the out-of-fold lung probability map. The split
contains 70 training cases and 22 mouse-grouped validation cases, and uses the
`3d_safe96` configuration with a 96 x 96 x 96 patch, batch size 2, and
`nnUNetTrainer_500epochs`.

## Startup verification

The five-epoch smoke test completed and reached pseudo-Dice 0.1281. The initial
full run on the C: drive completed its first epoch but stopped while writing a
PyTorch checkpoint. This was a storage-write failure, not a model or GPU-memory
failure. Generated nnU-Net results were therefore redirected to:

`D:\MouseLungLesionSeg_nnunet_results`

A subsequent startup attempt exposed Windows error 1455 because the paging file
was too small for multiple augmentation workers. Setting `nnUNet_n_proc_DA=1`
reduced host-memory pressure while leaving GPU model training unchanged.

The corrected run completed epoch 0 in 291.01 seconds:

| Measurement | Value |
|---|---:|
| Train loss | 0.0096 |
| Validation loss | -0.0691 |
| Pseudo-Dice | 0.0728 |
| Best-checkpoint size | 238.12 MB |
| GPU memory during training | approximately 4.0 / 8.0 GB |

The successful `checkpoint_best.pth` write on D: confirms that the earlier
checkpoint problem is resolved. These early training metrics are operational
signals only and must not be interpreted as final held-out performance.

## Reproducible launch settings

The run uses the existing `nnUNet_raw` and `nnUNet_preprocessed` directories in
the project workspace, with `nnUNet_results` pointing to the D: results folder
and `nnUNet_n_proc_DA=1`. Large checkpoints and logs remain local and should be
published through Zenodo rather than committed to GitHub.

## Next actions

1. Complete all 500 Fold 0 epochs and compare the saved-best and final
   checkpoints on the 22 held-out cases.
2. Export Fold 0 lesion probabilities and record case-level metrics and visual
   error analysis.
3. Repeat the same protocol for lesion folds 1-4.
4. Assemble five-fold out-of-fold lesion predictions before uncertainty,
   longitudinal tracking, radiomics, or phenotype analysis.
