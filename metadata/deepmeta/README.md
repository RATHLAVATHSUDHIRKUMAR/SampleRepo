# Public DeepMeta metadata

This directory contains small, non-image artifacts needed to reproduce the
DeepMeta conversion and mouse-grouped validation design.

Included:

- archive conversion summary;
- sanitized case manifest without local filesystem paths;
- lung and lesion grouped cross-validation splits;
- nnU-Net dataset, fingerprint, and plans JSON files;
- anatomy-guided lesion dataset template.

Not included:

- raw or converted MRI and label volumes;
- the downloaded Zenodo ZIP;
- nnU-Net preprocessed arrays;
- probability maps or predictions;
- trained checkpoints;
- local environments or caches.

Download the source data from <https://doi.org/10.5281/zenodo.6805921> and verify
the archive MD5 `cd0b81da901d808f50886206da6dc253`. Run
`scripts/prepare_deepmeta.py` to rebuild the local NIfTI and nnU-Net structure,
then run `scripts/export_public_metadata.py` to regenerate this directory.
