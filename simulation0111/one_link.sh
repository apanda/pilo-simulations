exp=( bt/bt as-topos/1221 as-topos/1239 fat_tree/ft_4_arity/fat_tree_4_arity )
config_files=( config_bt.yml config_as.yml config_as.yml config_ft.yml )
out_name=( bt as_1221 as_1239 fat_tree_4_arity )

for i in ${!exp[@]}; do
    for num in 4; do 
	e=${exp[$i]}
	cf=${config_files[$i]}
	fname=${out_name[$i]}
	dir="outputs/one_link"
	echo "python perturbation_noboot_1link.py $e$num.yaml 0 10000 1000 128 1024 1024 1 42 true $cf > $dir/$fname$num.output"
	python perturbation_noboot_1link.py $e$num.yaml 0 1000 10000 128 1024 1024 1 42 true $cf > $dir/$fname$num.output
    done
done
