## Trace NoC: Communication Trace Extraction for NoC Simulation

This is an unofficial fork of Gem5 where `trace-gem5` branch of gem5 has been extended to enable the extraction of network traces from any gem5 simulation mode (including legacy `fs.py` or `se.py`). These traces can be preprocessed and used as input for any Network-on-Chip (NoC) simulator such as [Noxim](https://github.com/davidepatti/noxim).

---

## Overview

With this repository, you can:

1. Run gem5 simulations in any mode (full system or syscall emulation).
2. Automatically dump network communication traces from the simulation.
3. Preprocess the trace data for use in Network-on-Chip simulators like [Noxim](https://github.com/davidepatti/noxim).

The tool provides a bridge between gem5 simulation and NoC simulation, allowing users to model traffic patterns and evaluate NoC performance under real application workloads.

---

## How to Use

### Clone gem5 Repository

Clone the gem5 repository and checkout the `trace-gem5` branch:
```bash
git clone https://github.com/hansikaweerasena/gem5-n.git
cd gem5
git checkout trace-gem5
```

### Build gem5

Build gem5 using the following command:
```bash
scons build/X86/gem5.opt -j {no_cpus}
```

### Run a Benchmark

Run your benchmark as the workload for your simulation. Below is an example command for running the **FFT** benchmark in system emulation mode on a 64-node MPSoC:
```bash
./build/X86/gem5.opt --debug-flags=RubyNetworkTrace --debug-file="./64_FFT_trace.txt" \
./configs/example/se.py --cmd="./benchmarks/FFT" --num-cpus=64 --num-dirs=64 --cpu-clock=2GHz \
--caches --l1d_size=32kB --l1i_size=32kB --l2cache --num-l2cache=64 --l2_size=512kB \
--mem-type=SimpleMemory --mem-size=4GB --ruby --network=simple --topology=Mesh_XY \
--mesh-rows=8 --link-latency=1 -m=2000000000
```

This command generates a `64_FFT_trace.txt` log file containing the network trace.

---

## Trace Format

The log file includes network traces in the following format:
```text
1500: PerfectSwitch-0: {cycle: 3, inOut: In, resReq: req, src: 0, srcType: L1Cache, des: [6], memAddr: 168576, size: Control, type: GET_INSTR}
2500: PerfectSwitch-2: {cycle: 5, inOut: Out, resReq: req, src: 0, srcType: L1Cache, des: [6], memAddr: 168576, size: Control, type: GET_INSTR}
4500: PerfectSwitch-2: {cycle: 9, inOut: In, resReq: req, src: 2, srcType: L2Cache, des: [10], memAddr: 168576, size: Control, type: GETS}
4500: PerfectSwitch-2: {cycle: 9, inOut: Out, resReq: req, src: 2, srcType: L2Cache, des: [10], memAddr: 168576, size: Control, type: GETS}
```

- Each log entry represents a single network trace extracted from the **boundary links** of the NoC. 
- **Inbound** messages refer to packets entering the NoC, and **outbound** messages refer to packets leaving the NoC. Internal hops within the NoC are **not recorded**.

### Example Entry Breakdown

For example, consider the second entry:
```text
2500: PerfectSwitch-2: {cycle: 5, inOut: Out, resReq: req, src: 0, srcType: L1Cache, des: [6], memAddr: 168576, size: Control, type: GET_INSTR}
```

- **2500**: Simulation time (in cycles).
- **PerfectSwitch-2**: The switch where the event occurred.
- **cycle**: The simulation cycle when the event occurred.
- **inOut**: The direction of the packet (inbound or outbound).
- **resReq**: Specifies whether the message is a response or a request.
- **src**: Source node ID.
- **srcType**: Type of the source (e.g., L1Cache, L2Cache).
- **des**: Destination node IDs.
- **memAddr**: Memory address associated with the request.
- **size**: Size/type of the message.
- **type**: Type of operation (e.g., GET_INSTR, GETS).

---

## Limitations

- **Single Processor Support**  
  Trace modeling currently supports programs running on a **uniprocessor**. For simulations involving multiple programs, you can simulate network traffic by creating **multiple instances of the traces** in the NoC simulator. Each instance will behave as a separate program.

---

## Contributions

Feel free to contribute by extending support for multi-processor simulations or improving the preprocessing pipeline. Open a pull request or report issues in this branch for discussion.

---

## References

- [gem5 Official Repository](https://gem5.org)
- [Noxim NoC Simulator](https://github.com/davidepatti/noxim)
