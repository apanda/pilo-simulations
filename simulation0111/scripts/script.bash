#!/bin/bash
input_folder=$1

rm data.ele data.gos data.paxos data_paxos_avail data.ideal

for f in $input_folder/*
do 
	if [[ $f =~ $input_folder/ex0.* ]]
	then
		python perturb_reachability_stats.py $f >> data.ele
	fi

	if [[ $f =~ $input_folder/ex3.* ]]
	then
		python perturb_reachability_stats.py $f >> data.gos
	fi

	if [[ $f =~ $input_folder/ex4.* ]]
	then
		python perturb_reachability_stats.py $f >> data.paxos
		python paxos_stats.py $f >> data_paxos_avail
	fi

	if [[ $f =~ $input_folder/ex5.* ]]
	then
		python perturb_reachability_stats.py $f >> data.ideal
	fi
done

gnuplot -e "filename='data'" graph.gnuplot
