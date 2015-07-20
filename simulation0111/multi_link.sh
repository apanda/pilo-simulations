exp=( bt/bt as-topos/1221 as-topos/1239 fat_tree/ft_4_arity/fat_tree_4_arity )
config_files=( config_bt.yml config_as.yml config_as.yml config_ft.yml )
out_name=( bt as_1221 as_1239 fat_tree_4_arity )

for i in ${!exp[@]}; do
    for num in 3 4; do 
	e=${exp[$i]}
	cf=${config_files[$i]}
	fname=${out_name[$i]}
	echo "python perturbation_noboot.py $e$num.yaml 0 300000 3600000 600000 600001 3 1000 42 true $cf > outputs/multi_link/$fname$num.output"
	python perturbation_noboot.py $e$num.yaml 0 300000 3600000 600000 600001 3 1000 42 true $cf > outputs/multi_link/$fname$num.output
    done
done
