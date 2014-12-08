#!/bin/bash
arg=$1
mttr=$2
outpfx=$3

#for i in $arg
  #do
./run_ex_n.bash simulation_tests/partset$arg/partset$arg $outpfx/partset$arg $mttr
wait
#done
