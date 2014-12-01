#!/bin/bash
prefix=$1
outprefix=$2
recovery=$3
SEED=42
for idx in 0 3 4 5
  do
    file="$prefix$idx"
    file+=".yaml"
    echo $file
#Usage: perturbation_extreme.py setup stable_time links_to_fail mean_recovery wait_at_end begin_mean_perturb
#end_mean_perturn step_mean_perturb sampling rate seed
    python -u perturbation_extreme.py $file 750.0 250 $recovery 14000000.0 150.0 300.0 150.0 500.0 $SEED > $outprefix/ex$idx.0 &
    python -u perturbation_extreme.py $file 750.0 250 $recovery 14000000.0 300.0 600.0 150.0 500.0 $SEED > $outprefix/ex$idx.1 &
    python -u perturbation_extreme.py $file 750.0 250 $recovery 14000000.0 600.0 900.0 150.0 500.0 $SEED > $outprefix/ex$idx.2 &
    python -u perturbation_extreme.py $file 750.0 250 $recovery 14000000.0 900.0 1200.0 150.0 500.0 $SEED > $outprefix/ex$idx.3 &
    python -u perturbation_extreme.py $file 750.0 250 $recovery 14000000.0 1200.0 1500.0 150.0 500.0 $SEED > $outprefix/ex$idx.4 &
  done
