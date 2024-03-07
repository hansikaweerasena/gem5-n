#!/bin/bash

# Define the list of benchmarks
benchmarks=("FFT" "FMM" "RADIX" "OCEAN" "BARNES" "LU")

# Loop over the list of benchmarks
for benchmark in "${benchmarks[@]}"
do
    echo "Running benchmark: $benchmark"
    ../build/X86/gem5.debug --debug-flags=RubyNetworkTrace --debug-file="/home/hansika/Research/gem5-n/64_${benchmark}_trace.txt" /home/hansika/Research/gem5-n/configs/example/se.py --cmd="/home/hansika/Research/gem5-n/benchmarks/$benchmark" --num-cpus=64 --num-dirs=64 --cpu-clock=2GHz --caches --l1d_size=32kB --l1i_size=32kB --l2cache --num-l2cache=64 --l2_size=512kB --mem-type=SimpleMemory --mem-size=4GB --ruby --network=simple --topology=Mesh_XY --mesh-rows=8 --link-latency=1 -m=2000000000
done

echo "Running benchmark: blackscholes"
../build/X86/gem5.debug --debug-flags=RubyNetworkTrace --debug-file="/home/hansika/Research/gem5-n/64_blackscholes_trace.txt" /home/hansika/Research/gem5-n/configs/example/se.py --cmd="/home/hansika/Research/gem5-n/benchmarks/parsec/blackscholes" -o '1 /home/hansika/Research/gem5-n/benchmarks/parsec/in_4K.txt /home/hansika/Research/gem5-n/benchmarks/parsec/prices.txt' --num-cpus=64 --num-dirs=64 --cpu-clock=2GHz --caches --l1d_size=32kB --l1i_size=32kB --l2cache --num-l2cache=64 --l2_size=512kB --mem-type=SimpleMemory --mem-size=4GB --ruby --network=simple --topology=Mesh_XY --mesh-rows=8 --link-latency=1 -m=2000000000