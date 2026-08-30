# Lung Fold 3 Interpretation

## Selected result

Fold 3 evaluated 18 mouse-grouped validation scans. The selected saved-best
checkpoint achieved mean Dice 0.8411, median Dice 0.9666, minimum Dice 0.0987,
and maximum Dice 0.9806. Six cases scored below both 0.90 and 0.85. All 18
out-of-fold probability maps were exported.

## Checkpoint interpretation

The saved-best checkpoint exceeded the final checkpoint in mean Dice (0.8411
versus 0.8095) and median Dice (0.9666 versus 0.9609). The improvement was
concentrated rather than uniform: the best checkpoint improved 6 of 18 cases,
while the final checkpoint was slightly better on 12. One case improved by
0.2971 and accounted for most of the +0.0316 mean difference; the largest loss
under the selected checkpoint was only 0.0083.

## Interpretation

The very high median indicates accurate segmentation for most Fold 3 scans, but
the low mean and minimum expose a substantial failure tail. One scan remained a
severe failure near Dice 0.0987 under both checkpoints, suggesting a case-specific
problem that additional epochs did not resolve. Plausible factors include
atypical anatomy, weak contrast, acquisition artifact, annotation disagreement,
or preprocessing sensitivity; these remain hypotheses until the source scan and
reference are reviewed directly.

## Implications

Fold 3 strongly supports retaining lung output as probabilistic anatomical
guidance rather than a hard gate. A hard mask derived from the severe failure
could suppress valid lesion predictions across much of the lung. The failed case
should receive a downstream uncertainty and quality-control flag.

## Limitations

The selected checkpoint is preferred by aggregate performance but is not
uniformly better. Fold 3 must remain part of the final pooled analysis so that
the reported result reflects both the high typical accuracy and the clinically
relevant failure tail. Fold 4 is required before drawing final lung-stage
generalization conclusions.
