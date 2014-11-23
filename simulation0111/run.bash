#!/bin/bash
prefix=$1
trace=$2
outprefix=$3
for idx in 0 3 4
  do
    file="$prefix$idx"
    file+=".yaml"
    echo $file
    python -u perturbation.py $file $trace 750.0 150.0 1500.0 150.0 > $outprefix/$idx 42 &
  done
