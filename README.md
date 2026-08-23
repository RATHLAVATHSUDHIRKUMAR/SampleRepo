# Mouse T2W MRI Lung Lesion Segmentation

A two-stage nnU-Net v2 pipeline for segmenting the lungs and lung lesions in mouse T2-weighted (T2W) MRI.

> **Research use only:** This software and the accompanying models are not medical devices and have not been validated for clinical diagnosis or treatment.

## Architecture specification

See [ARCHITECTURE_AND_PIPELINE.md](ARCHITECTURE_AND_PIPELINE.md) for the proposed
anatomy-guided 3D architecture, mouse-grouped validation design, uncertainty
estimation, longitudinal lesion tracking, and radiogenomic validation boundary.

## Pipeline

```text
T2W MRI (*_0000.nii.gz)
        |----------------------|
        v                      v
  Lung nnU-Net          Lesion nnU-Net
        |                      |
        |------ merge ---------|
                  v
       0 background / 1 lung / 2 lesion
```

The lung and lesion models receive the same input MRI. The merge step retains predicted lesion voxels only within the predicted lung mask.

## Repository contents

The GitHub repository contains only source code and documentation. Trained weights, extracted model folders, example MRI volumes, and generated predictions are intentionally excluded from Git.

```text
.
|-- models/
|   `-- README.md              # model download and extraction instructions
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


