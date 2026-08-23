# DeepMeta dataset audit and training protocol

## Provenance and integrity

- Official record: Zenodo `10.5281/zenodo.6805921`
- Local archive: `data/raw/deepmeta/deepmeta_dataset.zip`
- Expected and verified MD5: `cd0b81da901d808f50886206da6dc253`
- ZIP integrity test: passed

The images are 3D self-gated balanced steady-state free-precession (SG-bSSFP)
MRI. They are not conventional spin-echo T2-weighted acquisitions; results must
not be described as validated across arbitrary T2 MRI protocols.

## Released data audit

The archive contains 182 raw 128 x 128 x 128 uint8 TIFF stacks, metadata for
185 source IDs, and 14 NIfTI test images. IDs 8, 28, and 56 are represented by
the held-out test release rather than raw TIFF stacks.

The TIFF annotation folders contain released lung labels for 103 raw stacks.
Among those 103 cases, 41 are marked metastatic and 62 healthy. Lesion masks
are available for 30 metastatic cases. The other 11 metastatic scans are
excluded from supervised lesion training because absence of a released mask is
not evidence of an empty mask. Healthy cases are valid lesion-negative cases.

The paper/Zenodo description and the machine-readable archive differ in their
headline counts. All generated manifests therefore report what is physically
present and auditable in this archive, rather than assuming the prose count.

## Physical geometry and conversion

The acquisition field of view and matrix imply NIfTI spacing of 0.15625 x
0.15625 x 0.1953125 mm in x/y/z, with a voxel volume of 0.00476837158203125
mm3. `scripts/prepare_deepmeta.py` reconstructs masks using the release's global
slice index convention (`source_id * 128 + z`) and writes:

- `Dataset201_DeepMetaLung`: 103 MRI/lung-label pairs.
- `lesion_guidance_staging`: 92 valid lesion examples (30 positive, 62 healthy).
- `deepmeta_manifest.csv`: provenance, annotation status, mouse, time point,
  mutation group, and voxel counts for every converted case.

## Leakage-safe validation

Five folds are made with `StratifiedGroupKFold(seed=2026)`, grouping all scans
from the same biological mouse. No mouse occurs in both train and validation
within any fold. Lung validation probabilities must be saved with nnU-Net's
`--npz` option. `scripts/build_guided_lesion_dataset.py` then creates channel 0
as MRI and channel 1 as the held-out lung foreground probability. It rejects
missing, duplicate, or ineligible predictions.

This makes the anatomy channel soft and probabilistic. It must not be converted
to a hard ROI during training. Test-time uncertainty should be estimated from
an ensemble of the five lesion folds (and optionally test-time augmentation),
using predictive entropy and fold disagreement. Probability calibration should
be assessed on held-out mice.

## Longitudinal and biological scope

`scripts/quantify_longitudinal.py` computes connected-component and total-volume
tables from valid released masks. Only four mice currently have two or more
usable, explicitly timed observations. Missing metastatic annotations remain
missing. Registration and individual predicted-lesion association should be
run after cross-validated predictions exist; sparse released ground truth alone
does not support complete tracks.

The `LacZ` versus `iL34c` comparison is preliminary biological-phenotype
validation only. It is neither a treatment-response endpoint nor radiogenomic
validation. Radiogenomics claims are reserved until matched per-mouse RNA and/or
pathology measurements, identifiers, sampling times, and a prospectively defined
analysis protocol are available.

## Training status

nnU-Net integrity checking and preprocessing completed for 2D and 3D full
resolution. A 3D fold-0 smoke run selected 80 training and 23 validation scans,
but the automatically planned 128-cubed patch consumed about 7.83/8 GB VRAM and
the laptop GPU reached 89 C before one epoch completed. It was stopped safely.
Full five-fold training should run on a cooled GPU with more memory, or after a
separately named and documented reduced-patch plan is benchmarked. No checkpoint
or downstream claim is treated as complete from that interrupted run.
