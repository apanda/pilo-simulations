#!/bin/bash
arg=$1
mttr=$2
#for i in $arg
  #do 
    #./run.bash simulation_tests/set$i/set$i simulation_tests/"set$i"/"test$i""_ptrace" results_c32/set$i
    #wait
#done

for i in $arg
  do
    ./run_ex.bash simulation_tests/set$i/set$i results_c32_ex/set$i $mttr
    wait
done
