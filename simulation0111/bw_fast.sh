exp=( bt/bt as-topos/1221 fat_tree/ft_4_arity/fat_tree_4_arity )
config_files=( config_bt_fast.yml config_as_fast.yml config_ft_fast.yml )
out_name=( bt as_1221 fat_tree_4_arity )

#exp=( fat_tree/ft_4_arity/fat_tree_4_arity )
#config_files=( config_ft.yml )
#out_name=( fat_tree_4_arity )


for i in ${!exp[@]}; do
    e=${exp[$i]}
    cf=${config_files[$i]}
    fname=${out_name[$i]}
    num=3
    dir="outputs/bw_fast"
    echo "python perturbation_noboot.py $e$num.yaml 0 2000 600000 5000 10240000 10240000 1000 42 true $cf > $dir/$fname$num.output.5s"

    stdbuf -o0 python perturbation_noboot.py $e$num.yaml 0 2000 600000 5000 10240000 10240000 1000 42 true $cf > $dir/$fname$num.output.5s

    # echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.1min"

    # python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw/$fname$num.output.1min

    # echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw/$fname$num.output.10min"

    # python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw/$fname$num.output.10min

done

# MTTF = 5s, MTTR = 2s, runtime = 10 min
