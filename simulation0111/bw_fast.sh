exp=( bt/bt )
config_files=( config_bt_fast.yml  )
out_name=( bt  )

for i in ${!exp[@]}; do
    e=${exp[$i]}
    cf=${config_files[$i]}
    fname=${out_name[$i]}
    num=3
    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 30000 10240000 10240000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.30s"

    python perturbation_noboot.py $e$num.yaml 0 300000 1800000 30000 10240000 10240000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.30s

    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.1min"

    python perturbation_noboot.py $e$num.yaml 0 300000 1800000 60000 10240000 10240000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.1min

    echo "python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.10min"

    python perturbation_noboot.py $e$num.yaml 0 300000 1800000 600000 10240000 102400000 1000 42 true $cf > outputs/bw_fast/$fname$num.output.10min

done
