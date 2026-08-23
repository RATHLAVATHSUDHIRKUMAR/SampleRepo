# Models

Trained model weights are hosted on Zenodo and are intentionally excluded from GitHub.

1. Download `models.zip` from:

   `TODO: add the Zenodo record or direct models.zip URL`

2. Extract the archive directly into this `models/` directory:

   ```bash
   unzip /path/to/models.zip -d models
   ```

3. Confirm that these paths exist:

   ```text
   models/mouse_lung_model/inference_nnUNet.sh
   models/mouse_lung_model/nnUNet_results/Dataset101_mice_final/
   models/mouse_lung_lesion_model/inference_nnUNet.sh
   models/mouse_lung_lesion_model/nnUNet_results/Dataset101_MRI-Lung/
   ```

There should not be a nested `models/models/` directory. See the repository's main `README.md` for installation and inference commands.

All other contents of this directory are ignored by Git.
