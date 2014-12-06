#!/bin/bash
arg=$1
mttr=$2
outpfx=$3

#for i in $arg
  #do
./run_ex.bash simulation_tests/partset$i/partset$i $3/partset$i $mttr
wait
#done
