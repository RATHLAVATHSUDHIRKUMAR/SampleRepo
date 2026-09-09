# Anatomy-Guided Lesion Fold 2 Training Status

Status date: 2026-09-08

Fold 2 completed all 500 epochs using 76 training cases and 16 mouse-grouped
validation cases. The automatic final-checkpoint validation produced mean
foreground Dice 0.2986. The highest training-time EMA pseudo-Dice was 0.4994.

Both `checkpoint_best.pth` and `checkpoint_final.pth` were written successfully
to local D: storage. The saved-best checkpoint has not yet received the same
held-out inference evaluation, so checkpoint selection and probability export
remain pending. No Fold 2 result should be treated as final until that paired
comparison is complete.

## Next actions

1. Validate the saved-best checkpoint on the same 16 cases.
2. Compare final and saved-best case-level Dice and detection behavior.
3. Export soft probabilities from the selected checkpoint.
4. Preserve large predictions and checkpoints locally/for Zenodo and commit
   only sanitized metrics and interpretation to GitHub.

