# Lung Fold 1 Interpretation

## Selected result

Fold 1 evaluated 22 mouse-grouped validation scans. The selected saved-best
checkpoint achieved mean Dice 0.8414, median Dice 0.9338, minimum Dice 0.2325,
and maximum Dice 0.9803. Eight cases scored below 0.90 and five scored below
0.85. All 22 out-of-fold probability maps were exported.

## Checkpoint interpretation

The saved-best checkpoint exceeded the final checkpoint in mean Dice (0.8414
versus 0.8300) and median Dice (0.9338 versus 0.9155). The paired result was not
uniform: the saved-best checkpoint improved 8 cases and the final checkpoint
was better on 14. A single difficult scan improved by 0.2551 and contributed
substantially to the higher selected mean. The checkpoint was therefore selected
by aggregate validation performance, not because it improved every scan.

## Interpretation

The gap between the median and minimum shows that Fold 1 contains a difficult
subgroup. Most cases remain useful for anatomical guidance, but the weakest
predictions cannot be treated as dependable hard anatomical boundaries. Fold 1
also demonstrates why checkpoint selection must use held-out case metrics rather
than only the final epoch or a training-time average.

## Implications and limitations

The selected probability maps should be passed to the lesion model as a soft
channel. The low-performing cases should receive explicit uncertainty or
quality-control flags downstream. Fold 1 supports the architecture but also
shows meaningful between-fold heterogeneity that must be retained in the final
five-fold summary.
