# nnU-Net model-folder structure

The Zenodo staging area contains three self-contained model folders modeled on the `Ovary-Cyst_AI_model` package. Each folder has the nnU-Net environment directories and an inference script at its root:

```text
MODEL_PACKAGE/
|-- inference_nnUNet.sh
|-- inference_nnUNet_original.sh
|-- nnUNet_raw/
|   `-- DatasetXXX_Name/
|       |-- dataset.json
|       |-- imagesTe/
|       `-- labelsTe/
|-- nnUNet_preprocessed/
`-- nnUNet_results/
    `-- DatasetXXX_Name/
        `-- TRAINER__PLANS__3d_fullres/
            |-- dataset.json
            |-- dataset_fingerprint.json
            |-- plans.json
            `-- fold_NAME/
                |-- checkpoint_final.pth
                |-- debug.json
                `-- progress.png
```

The three staged packages are:

```text
zenodo_assets/model_folders/
|-- mouse_lung_model/
|   `-- nnUNet_results/Dataset101_mice_final/
|       `-- nnUNetTrainer__nnUNetPlans__3d_fullres/fold_all/
|-- mouse_lung_lesion_resenc_fold_all/
|   `-- nnUNet_results/Dataset101_MRI-Lung/
|       `-- nnUNetTrainer__nnUNetResEncUNetMPlans__3d_fullres/fold_all/
`-- mouse_lung_lesion_5fold/
    `-- nnUNet_results/Dataset103_MRI-Lung/
        `-- nnUNetTrainer__nnUNetPlans__3d_fullres/
            |-- fold_0/
            |-- fold_1/
            |-- fold_2/
            |-- fold_3/
            `-- fold_4/
```

Only `checkpoint_final.pth` is distributed, matching the nnU-Net inference default selected for this release.

## Run a model folder

Install nnU-Net, activate the environment, put single-channel inputs named `CASE_0000.nii.gz` into the package's `nnUNet_raw/.../imagesTe/` directory, and submit:

```bash
cd /path/to/MODEL_PACKAGE
sbatch inference_nnUNet.sh
```

For a non-SLURM run:

```bash
cd /path/to/MODEL_PACKAGE
bash inference_nnUNet.sh
```

You may override the default paths and device:

```bash
INPUT_DIR=/path/to/imagesTs \
OUTPUT_DIR=/path/to/predictions \
DEVICE=cuda \
bash inference_nnUNet.sh
```

The package-local script computes all three nnU-Net environment paths from its own location. `inference_nnUNet_original.sh` is retained only as a record of the original cluster command and contains NIH-specific paths; use `inference_nnUNet.sh` for the distributable package.

The previously generated individual ZIP archives follow the official `nnUNetv2_export_model_to_zip` layout for `nnUNetv2_install_pretrained_model_from_zip`. The new `model_folders/` hierarchy is the manual, self-contained layout requested for Zenodo and matches the structure of the ovary reference package.

