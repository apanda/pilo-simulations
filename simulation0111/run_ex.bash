#!/bin/bash
prefix=$1
outprefix=$2
for idx in 0 3 4 5
  do
    file="$prefix$idx"
    file+=".yaml"
    echo $file
#Usage: perturbation_extreme.py setup stable_time links_to_fail mean_recovery wait_at_end begin_mean_perturb
#end_mean_perturn step_mean_perturb seed
    python -u perturbation_extreme.py $file 200.0 250 210.0 10000.0  750.0 150.0 300.0 150.0 42 > $outprefix/$idx.0 &
    python -u perturbation_extreme.py $file 200.0 250 210.0 10000.0  750.0 300.0 600.0 150.0 42 > $outprefix/$idx.1 &
    python -u perturbation_extreme.py $file 200.0 250 210.0 10000.0  750.0 600.0 900.0 150.0 42 > $outprefix/$idx.2 &
    python -u perturbation_extreme.py $file 200.0 250 210.0 10000.0  750.0 900.0 1200.0 150.0 42 > $outprefix/$idx.3 &
    python -u perturbation_extreme.py $file 200.0 250 210.0 10000.0  750.0 1200.0 1500.0 150.0 42 > $outprefix/$idx.4 &
  done
