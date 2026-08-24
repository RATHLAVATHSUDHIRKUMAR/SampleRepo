# Mouse T2W MRI Lung Lesion Segmentation

A research repository for lung and pulmonary-lesion segmentation in mouse MRI.
It contains the existing legacy inference pipeline and an advanced anatomy-guided
3D architecture that is currently being trained and validated.

> **Research use only:** This software and the accompanying models are not medical devices and have not been validated for clinical diagnosis or treatment.

## Architecture versions

### Legacy architecture

The legacy pipeline runs the lung and lesion models independently on the same
MRI. It then clips the predicted lesion mask to the predicted lung mask and
merges both outputs.

```text
Mouse MRI (*_0000.nii.gz)
        |----------------------|
        v                      v
  Lung nnU-Net          Lesion nnU-Net
        |                      |
        |---- hard-mask merge -|
                  v
       0 background / 1 lung / 2 lesion
```

This architecture is retained for compatibility with the existing packaged
models and inference scripts. A limitation is that hard lung-mask clipping can
remove lesions near uncertain lung or pleural boundaries.

### Advanced architecture under development

The advanced pipeline uses the lung prediction as soft anatomical guidance for
the lesion model:

#### Why move to the advanced architecture?

The legacy pipeline is useful for inference with the existing packaged models,
but its independent-model and hard-merge design limits the intended research
workflow:

1. **Hard-mask error propagation.** If the lung model excludes a true lung or
   pleural region, the merge step automatically removes any lesion prediction
   in that region. The lesion model cannot recover from the lung error.
2. **No anatomical conditioning during lesion learning.** The legacy lesion
   model sees MRI alone. It does not learn how uncertain lung anatomy should
   influence lesion probability.
3. **Small and boundary lesions are vulnerable.** Mouse pulmonary lesions can
   occupy very few voxels and may lie near lung boundaries. A continuous lung
   probability provides graded context instead of an all-or-nothing ROI.
4. **No explicit uncertainty output.** A single hard prediction cannot
   distinguish confident tumor from disagreement between models. Fold ensembles
   provide probability variance and predictive entropy for quality control.
5. **Scan-level segmentation is insufficient for longitudinal studies.** The
   legacy pipeline reports masks and aggregate burden but does not integrate
   registration, individual-lesion association, growth, resolution, or new
   lesion events.
6. **Validation can leak repeated-mouse information.** Random scan or slice
   splitting can place different time points from one mouse in training and
   validation. The advanced protocol groups every time point by biological
   mouse and uses out-of-fold lung probabilities for lesion training.
7. **Downstream phenotype analysis needs reproducible confidence-aware ROIs.**
   Longitudinal volume, radiomics, and future RNA/pathology association require
   traceable physical-space masks, uncertainty estimates, and clearly separated
   validation stages.

The advanced design therefore changes the lung output from a final hard gate
into a soft anatomical feature. It also extends segmentation into a controlled
mouse-grouped pipeline for uncertainty, longitudinal measurement, and eventual
biological validation. These improvements are hypotheses to be tested; they are
not assumed to outperform the legacy models until cross-validation is complete.

```text
Mouse 3D MRI
      |
      v
Preprocessing and quality control
      |
      v
Lung 3D nnU-Net
      |
      v
Soft lung probability P(lung)
      |-------------------|
      |                   |
      v                   v
MRI channel         Anatomy channel
      |                   |
      |------ [MRI + P(lung)]
                         |
                         v
             Anatomy-guided lesion model
                         |
              |----------|----------|
              v                     v
       Lesion probability      Uncertainty map
              |                     |
              |----------|----------|
                         v
             Confidence-aware lesions
                         |
                         v
          Registration and lesion tracking
                         |
              |----------|----------|
              v                     v
        Volume trajectory       Radiomics
              |                     |
              |----------|----------|
                         v
               Imaging phenotype
                         |
              |----------|----------|
              v                     v
     Preliminary IL34       Future matched RNA /
        comparison              pathology
                                      |
                                      v
                                Radiogenomics
```

Key differences from the legacy pipeline:

- The lesion model receives two channels: MRI and continuous `P(lung)`.
- Lung guidance is generated out of fold so that the same mouse cannot leak
  between model stages during validation.
- The soft anatomical map is not converted into a hard training ROI.
- Five-fold ensembles provide probability, disagreement, and entropy-based
  uncertainty.
- Longitudinal registration supports individual-lesion tracking and growth
  trajectories.
- The LacZ/iL34c comparison remains preliminary phenotype validation.
- Radiogenomic claims are reserved until matched RNA or pathology data exist.

The advanced architecture is not yet a released trained model. Lung fold
training is in progress; anatomy-guided lesion training and downstream model
validation follow after all out-of-fold lung probabilities are available.

See [ARCHITECTURE_AND_PIPELINE.md](ARCHITECTURE_AND_PIPELINE.md) for the complete
advanced specification and [DEEP_META_DATA_AUDIT.md](DEEP_META_DATA_AUDIT.md)
for the DeepMeta provenance, conversion, exclusions, and validation protocol.

## Repository contents

The GitHub repository contains only source code and documentation. Trained weights, extracted model folders, example MRI volumes, and generated predictions are intentionally excluded from Git.

The publication boundary is:

- **GitHub:** source code, documentation, configurations, grouped splits, and
  sanitized metadata.
- **Zenodo/local storage:** MRI images, labels, trained checkpoints,
  preprocessed arrays, probability maps, and other large generated artifacts.

```text
.
|-- models/
|   `-- README.md              # model download and extraction instructions
|-- metadata/deepmeta/         # public configs, splits, and sanitized metadata
|-- scripts/
|   |-- merge_masks.py
|   |-- total_tumor_burden.py
|   |-- package_inference_lung.sh
|   `-- package_inference_lesion_single.sh
|-- CITATION.cff
|-- LICENSE
|-- MODEL_FOLDER_STRUCTURE.md
|-- requirements.txt
`-- README.md
```

After downloading the model ZIP from Zenodo, the user adds the model packages under `models/` as described below.

## Installation

Python 3.10 or newer is recommended. Install PyTorch for your CUDA version first, then install the remaining dependencies:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/MouseLungLesionSeg.git
cd MouseLungLesionSeg

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

See the official [nnU-Net installation guide](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/getting-started/installation-and-setup.md) and [inference guide](https://github.com/MIC-DKFZ/nnUNet/blob/master/documentation/how-to/run-inference.md).

## Download the trained models from Zenodo

The trained model files are not stored in GitHub because the checkpoints are too large. Download the model archive from Zenodo:

> **Zenodo download:** `TODO: add the Zenodo record or direct models.zip URL`

The intended archive name is `models.zip`. Extract its contents directly into this repository's existing `models/` directory.

Linux or macOS:

```bash
unzip /path/to/models.zip -d models
```

Windows PowerShell:

```powershell
Expand-Archive -LiteralPath C:\path\to\models.zip -DestinationPath .\models
```

After extraction, verify that there is only one `models` directory—not `models/models`—and that the structure is:

```text
models/
|-- README.md
|-- mouse_lung_model/
|   |-- inference_nnUNet.sh
|   |-- Dataset/
|   `-- nnUNet_results/
|       `-- Dataset101_mice_final/
|           `-- nnUNetTrainer__nnUNetPlans__3d_fullres/
|               |-- dataset.json
|               |-- dataset_fingerprint.json
|               |-- plans.json
|               `-- fold_all/
|                   `-- checkpoint_final.pth
`-- mouse_lung_lesion_model/
    |-- inference_nnUNet.sh
    |-- Dataset/
    `-- nnUNet_results/
        `-- Dataset101_MRI-Lung/
            `-- nnUNetTrainer__nnUNetPlans__3d_fullres/
                |-- dataset.json
                |-- dataset_fingerprint.json
                |-- plans.json
                `-- fold_all/
                    `-- checkpoint_final.pth
```

Do not commit the extracted folders. The repository's `.gitignore` excludes everything under `models/` except `models/README.md`.

## Input format

Each input is a single-channel NIfTI image following nnU-Net naming:

```text
imagesTs/
|-- mouse001_0000.nii.gz
|-- mouse002_0000.nii.gz
`-- mouse003_0000.nii.gz
```

Case identifiers must be unique and files must end in `.nii.gz`.

## Run lung inference

The model package includes a SLURM-compatible inference script. Always provide `INPUT_DIR` because the downloaded package keeps example data in a generic `Dataset/` directory.

```bash
INPUT_DIR=/absolute/path/to/imagesTs \
OUTPUT_DIR=/absolute/path/to/lung_predictions \
DEVICE=cuda \
bash models/mouse_lung_model/inference_nnUNet.sh
```

On a SLURM cluster:

```bash
INPUT_DIR=/absolute/path/to/imagesTs \
OUTPUT_DIR=/absolute/path/to/lung_predictions \
DEVICE=cuda \
sbatch --export=ALL models/mouse_lung_model/inference_nnUNet.sh
```

## Run lesion inference

```bash
INPUT_DIR=/absolute/path/to/imagesTs \
OUTPUT_DIR=/absolute/path/to/lesion_predictions \
DEVICE=cuda \
bash models/mouse_lung_lesion_model/inference_nnUNet.sh
```

On a SLURM cluster:

```bash
INPUT_DIR=/absolute/path/to/imagesTs \
OUTPUT_DIR=/absolute/path/to/lesion_predictions \
DEVICE=cuda \
sbatch --export=ALL models/mouse_lung_lesion_model/inference_nnUNet.sh
```

Use `DEVICE=cpu` for CPU inference. GPU inference is recommended.

## Merge lung and lesion predictions

```bash
python scripts/merge_masks.py \
  --images /absolute/path/to/imagesTs \
  --lung-masks /absolute/path/to/lung_predictions \
  --lesion-masks /absolute/path/to/lesion_predictions \
  --output /absolute/path/to/combined_predictions
```

The combined masks use these labels:

| Value | Meaning |
|---:|---|
| 0 | Background |
| 1 | Lung without predicted lesion |
| 2 | Predicted lesion inside the predicted lung |

If prediction geometry differs from the input image, the merge utility resamples labels into the input image's physical space using nearest-neighbor interpolation.

## Model provenance

| Task | Dataset directory | Trainer/plans/configuration | Fold | Checkpoint |
|---|---|---|---|---|
| Lung | `Dataset101_mice_final` | `nnUNetTrainer__nnUNetPlans__3d_fullres` | `all` | `checkpoint_final.pth` |
| Lung lesion | `Dataset101_MRI-Lung` | `nnUNetTrainer__nnUNetPlans__3d_fullres` | `all` | `checkpoint_final.pth` |

The model archive includes the `dataset.json`, `dataset_fingerprint.json`, `plans.json`, and fold metadata required by nnU-Net.

### Preserved lung-model metadata

The original lung-model nnU-Net metadata names channel 0 `CT`, stores the internal dataset name as `Dataset101_mice`, and specifies `CTNormalization`. These training metadata are retained unchanged because nnU-Net uses the saved plans during inference. The public pipeline input remains a single T2W MRI named `*_0000.nii.gz`.

## Before making the repository public

- Replace the Zenodo placeholder with the model-record URL or DOI.
- Replace `YOUR-GITHUB-USERNAME` with the GitHub account or organization that owns `MouseLungLesionSeg`.
- Complete `CITATION.cff` with the author list, repository URL, DOI, and publication.
- Replace the placeholder `LICENSE` with the approved software and model license.
- Add training-data citations, funding acknowledgments, and the model-training nnU-Net version.
- Confirm that no restricted MRI data are included in the Git commit.

## Citation

If you use this pipeline, please cite this repository, the Zenodo model record, the associated publication, and [nnU-Net](https://github.com/MIC-DKFZ/nnUNet).


