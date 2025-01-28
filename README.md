## Trace NoC: Communication Trace Extraction for NoC Simulation

This branch of gem5 has been extended to enable the extraction of network traces from any gem5 simulation mode (including legacy `fs.py` or `se.py`). These traces can be preprocessed and used as input for any Network-on-Chip (NoC) simulator.

---

## Overview

With this repository, you can:

1. Run gem5 simulations in any mode (full system or syscall emulation).
2. Automatically dump network communication traces from the simulation.
3. Preprocess the trace data for use in Network-on-Chip simulators like [Noxim](https://github.com/davidepatti/noxim).

The tool provides a bridge between gem5 simulation and NoC simulation, allowing users to model traffic patterns and evaluate NoC performance under real application workloads.

---

## Usage

1. Clone the gem5 repository and checkout this branch.
2. Run gem5 simulations using your preferred configuration script (e.g., `fs.py` or `se.py`).
3. Extracted trace files will be saved automatically during the simulation.
4. Preprocess these trace files as needed for your NoC simulator.

---

## Limitations

- **Single Processor Support**:  
  Trace modeling currently supports programs running on a **uniprocessor**. For simulations involving multiple programs, you can simulate network traffic by creating **multiple instances of the traces** in the NoC simulator. Each instance will behave as a separate program.  

---

## Example Workflow

1. **Run gem5 simulation**:
   ```bash
   ./build/X86/gem5.opt configs/example/se.py --cmd=<your_program>

