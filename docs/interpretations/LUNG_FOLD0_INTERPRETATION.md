# Lung Fold 0 Interpretation

## Selected result

Fold 0 evaluated 23 mouse-grouped validation scans. The selected final
checkpoint achieved mean Dice 0.9176, median Dice 0.9770, minimum Dice 0.6359,
and maximum Dice 0.9850. Five cases scored below both 0.90 and 0.85. All 23
out-of-fold probability maps were exported.

## Interpretation

The high median indicates that the model segmented the lung accurately for most
held-out scans. The mean is lower than the median because five difficult cases
form a distinct low-performing tail. Consequently, the mean should not be read
as the performance of a typical case; the median better describes the central
behavior, while the minimum and threshold counts describe reliability.

Visual review localized much of the disagreement near the diaphragm,
mediastinal boundary, and outer lung margins. These are anatomically plausible
failure regions where image contrast and partial-volume effects can make the
reference boundary uncertain. The result supports the usefulness of learned
lung guidance but does not justify hard-mask clipping of lesion predictions.

## Implications

Fold 0 provides strong initial evidence that continuous lung probabilities can
serve as anatomical context for the lesion model. Boundary uncertainty should
remain encoded in the probability map so that pleural or boundary-adjacent
lesions are not automatically discarded.

## Limitations

This is one validation fold and cannot establish complete-dataset
generalization. The five low-performing cases must remain in aggregate reporting
and later uncertainty analysis. Conclusions should be combined with Folds 1–4
before reporting the final lung-stage performance.
