#exp=( bt/bt as-topos/1221 as-topos/1239 fat_tree/ft_4_arity/fat_tree_4_arity )
#config_files=( config_bt.yml config_as.yml config_as.yml config_ft.yml )
#out_name=( bt as_1221 as_1239 fat_tree_4_arity )

exp=( fat_tree/ft_4_arity/fat_tree_4_arity )
config_files=( config_ft.yml )
out_name=( fat_tree_4_arity )


for i in ${!exp[@]}; do
    e=${exp[$i]}
    cf=${config_files[$i]}
    fname=${out_name[$i]}
    num=3
    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 30000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.30s"

    stdbuf -o0 python perturbation_noboot.py $e$num.yaml 0 300000 1800000 30000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.30s

    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.1min"

    python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.1min

    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw/$fname$num.output.10min"

    python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw/$fname$num.output.10min

done
