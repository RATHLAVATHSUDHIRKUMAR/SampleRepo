# Lung Fold 4 Interpretation

## Selected result

Fold 4 evaluated 18 mouse-grouped validation scans. The selected final
checkpoint achieved mean Dice 0.8674, median Dice 0.9514, minimum Dice 0.2932,
and maximum Dice 0.9867. Five cases scored below 0.90 and three scored below
0.85. All 18 out-of-fold probability maps were exported.

## Checkpoint interpretation

The final and saved-best checkpoints were stable and nearly equivalent. The
final checkpoint exceeded the saved best in mean Dice (0.8674 versus 0.8669)
and median Dice (0.9514 versus 0.9480), and was better on 11 of 18 cases. The
small differences indicate that checkpoint choice does not materially alter the
overall Fold 4 conclusion.

## Interpretation

The high median indicates accurate lung segmentation for most held-out scans.
The lower mean reflects a failure tail dominated by two scans near Dice 0.30.
Because both checkpoints fail on the same cases, these errors are more likely
to reflect case-specific anatomy, acquisition, annotation, or preprocessing
conditions than ordinary late-epoch fluctuation. This attribution remains a
hypothesis until the source images and references are reviewed.

## Implications

Fold 4 reinforces the decision to use lung probability as soft anatomical
guidance. Hard masking would allow the two severe lung failures to suppress
potential lesion predictions. Their guidance maps should remain available but
must be accompanied by explicit uncertainty and scan-level quality flags.

## Five-fold conclusion

All 103 lung cases now have leakage-safe out-of-fold probability maps. Typical
performance is strong across folds, but Folds 1, 3, and 4 contain important
failure tails. The completed lung stage therefore supports anatomy-guided lesion
modeling while also demonstrating that uncertainty estimation and quality
control are required components rather than optional additions.
