#!/bin/bash
arg=$1
mttr=$2

for i in $arg
  do
    ./run_ex.bash simulation_tests/set$i/set$i results_c32_ex/set$i $mttr
    wait
done
