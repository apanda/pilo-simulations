#!/bin/bash
prefix=$1
trace=$2
outprefix=$3
SEED=42
for idx in 0 3 4
  do
    file="$prefix$idx"
    file+=".yaml"
    echo $file
    python -u perturbation.py $file $trace 750.0 600.0 900.0 150.0 $SEED > $outprefix/$idx.1 &
    python -u perturbation.py $file $trace 750.0 900.0 1500.0 150.0 $SEED > $outprefix/$idx.2 &
  done
