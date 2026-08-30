# Lung Fold 2 Interpretation

## Selected result

Fold 2 evaluated 22 mouse-grouped validation scans. The selected final
checkpoint achieved mean Dice 0.9047, median Dice 0.9316, minimum Dice 0.5092,
and maximum Dice 0.9838. Three cases scored below both 0.90 and 0.85. All 22
out-of-fold probability maps were exported.

## Checkpoint interpretation

The final checkpoint slightly exceeded the saved-best checkpoint in mean Dice
(0.9047 versus 0.9034) and median Dice (0.9316 versus 0.9297). More importantly,
the final checkpoint was better on 19 of 22 paired cases. The differences were
small—the largest final-checkpoint gain was 0.0054 and the largest saved-best
gain was 0.0024—indicating stable late-training performance rather than a large
checkpoint-dependent shift.

## Interpretation

Fold 2 shows comparatively consistent generalization. Its mean and median are
closer than those of Folds 1 and 3, and only three cases fall below Dice 0.85.
Nevertheless, the minimum Dice of 0.5092 confirms that a high fold-level average
does not guarantee dependable segmentation for every scan.

## Implications and limitations

The stability between checkpoints supports using the final model for
out-of-fold anatomical guidance. The three difficult scans must remain visible
in uncertainty analysis and should not be removed to improve the aggregate
score. Final claims still require the combined five-fold distribution.
