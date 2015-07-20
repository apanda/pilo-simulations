exp=( fat_tree/ft_4_arity/fat_tree_4_arity )
config_files=( config_ft_fast.yml )
out_name=( fat_tree_4_arity )

for i in ${!exp[@]}; do
    e=${exp[$i]}
    cf=${config_files[$i]}
    fname=${out_name[$i]}
    num=3
    echo "python perturbation_noboot.py $e$num.yaml 0 300000 600000 30000 10240000 10240000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.30s"

    python perturbation_noboot.py $e$num.yaml 0 300000 600000 30000 10240000 10240000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.30s

    echo "python perturbation_noboot.py $e$num.yaml 0 300000 600000 60000 10240000 10240000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.1min"

    python perturbation_noboot.py $e$num.yaml 0 300000 600000 60000 10240000 10240000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.1min


    echo "python perturbation_noboot.py $e$num.yaml 0 300000 600000 300000 10240000 102400000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.5min"

    python perturbation_noboot.py $e$num.yaml 0 300000 600000 300000 10240000 102400000 1000 42 true $cf > outputs/bw_faster/$fname$num.output.5min


done
