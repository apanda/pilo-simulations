# exp=( bt/bt as-topos/1221 fat_tree/ft_4_arity/fat_tree_4_arity )
# config_files=( config_bt_fast.yml config_as_fast.yml config_ft_fast.yml )
# out_name=( bt as_1221 fat_tree_4_arity )

exp=( fat_tree/ft_8_arity/fat_tree_8_arity_4_controller fat_tree/ft_8_arity/fat_tree_8_arity)
config_files=( config_ft.yml config_ft.yml )
out_name=( fat_tree_8_arity_4_controller fat_tree_8_arity_8_controller )


for i in ${!exp[@]}; do
    e=${exp[$i]}
    cf=${config_files[$i]}
    fname=${out_name[$i]}
    num=3
    dir="outputs/bw_normal"
    echo "python perturbation_noboot.py $e$num.yaml 0 20000 600000 60000 10240000 10240000 1000 42 true $cf > $dir/$fname$num.output"

    stdbuf -o0 python perturbation_noboot.py $e$num.yaml 0 20000 600000 60000 10240000 10240000 1000 42 true $cf > $dir/$fname$num.output

done

# MTTF = 5s, MTTR = 2s, runtime = 10 min
