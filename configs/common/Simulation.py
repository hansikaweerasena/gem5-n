# Copyright (c) 2012-2013 ARM Limited
# All rights reserved
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2006-2008 The Regents of The University of Michigan
# Copyright (c) 2010 Advanced Micro Devices, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
from os import getcwd
from os.path import join as joinpath

from common import CpuConfig
from common import ObjectList

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.util import *

addToPath("../common")


def getCPUClass(cpu_type):
    """Returns the required cpu class and the mode of operation."""
    cls = ObjectList.cpu_list.get(cpu_type)
    return cls, cls.memory_mode()


def setCPUClass(options):
    """Returns two cpu classes and the initial mode of operation.

    Restoring from a checkpoint or fast forwarding through a benchmark
    can be done using one type of cpu, and then the actual
    simulation can be carried out using another type. This function
    returns these two types of cpus and the initial mode of operation
    depending on the options provided.
    """

    TmpClass, test_mem_mode = getCPUClass(options.cpu_type)
    CPUClass = None
    if TmpClass.require_caches() and not options.caches and not options.ruby:
        fatal("%s must be used with caches" % options.cpu_type)

    if options.checkpoint_restore != None:
        if options.restore_with_cpu != options.cpu_type:
            CPUClass = TmpClass
            TmpClass, test_mem_mode = getCPUClass(options.restore_with_cpu)
    elif options.fast_forward:
        CPUClass = TmpClass
        TmpClass = AtomicSimpleCPU
        test_mem_mode = "atomic"

    # Ruby only supports atomic accesses in noncaching mode
    if test_mem_mode == "atomic" and options.ruby:
        warn("Memory mode will be changed to atomic_noncaching")
        test_mem_mode = "atomic_noncaching"

    print('---------------------------------------')
    print(test_mem_mode)

    return (TmpClass, test_mem_mode, CPUClass)


def setMemClass(options):
    """Returns a memory controller class."""

    return ObjectList.mem_list.get(options.mem_type)


def setWorkCountOptions(system, options):
    if options.work_item_id != None:
        system.work_item_id = options.work_item_id
    if options.num_work_ids != None:
        system.num_work_ids = options.num_work_ids
    if options.work_begin_cpu_id_exit != None:
        system.work_begin_cpu_id_exit = options.work_begin_cpu_id_exit
    if options.work_end_exit_count != None:
        system.work_end_exit_count = options.work_end_exit_count
    if options.work_end_checkpoint_count != None:
        system.work_end_ckpt_count = options.work_end_checkpoint_count
    if options.work_begin_exit_count != None:
        system.work_begin_exit_count = options.work_begin_exit_count
    if options.work_begin_checkpoint_count != None:
        system.work_begin_ckpt_count = options.work_begin_checkpoint_count
    if options.work_cpus_checkpoint_count != None:
        system.work_cpus_ckpt_count = options.work_cpus_checkpoint_count




def run(options, root, testsys, cpu_class):
    # Setup global stat filtering.
    stat_root_simobjs = []
    for stat_root_str in options.stats_root:
        stat_root_simobjs.extend(root.get_simobj(stat_root_str))
    m5.stats.global_dump_roots = stat_root_simobjs

    np = options.num_cpus
    switch_cpus = None

    testsys.exit_on_work_items = True     
    print("switching")
    switch_cpus = [
                    TimingSimpleCPU(switched_out=True, cpu_id=(i)) for i in range(np)
                ]
    # print(switch_cpus)
    for i in range(np):
        switch_cpus[i].system = testsys
        switch_cpus[i].workload = testsys.cpu[i].workload
        switch_cpus[i].clk_domain = testsys.cpu[i].clk_domain
        switch_cpus[i].isa = testsys.cpu[i].isa

        # testsys.cpu[i].max_insts_any_thread = 1
        switch_cpus[i].createThreads()

    testsys.switch_cpus = switch_cpus
    switch_cpu_list = [(testsys.cpu[i], switch_cpus[i]) for i in range(np)]
    # print(switch_cpu_list)

    root.apply_config(options.param)
    m5.instantiate(None)
    
    # Initialization is complete.  If we're not in control of simulation
    # (that is, if we're a slave simulator acting as a component in another
    #  'master' simulator) then we're done here.  The other simulator will
    # call simulate() directly. --initialize-only is used to indicate this.
    if options.initialize_only:
        return

    # Handle the max tick settings now that tick frequency was resolved
    # during system instantiation
    # NOTE: the maxtick variable here is in absolute ticks, so it must
    # include any simulated ticks before a checkpoint
    explicit_maxticks = 0
    maxtick_from_abs = m5.MaxTick
    maxtick_from_rel = m5.MaxTick
    maxtick_from_maxtime = m5.MaxTick
    if options.abs_max_tick:
        maxtick_from_abs = options.abs_max_tick
        explicit_maxticks += 1
    if options.rel_max_tick:
        maxtick_from_rel = options.rel_max_tick
        if options.checkpoint_restore:
            # NOTE: this may need to be updated if checkpoints ever store
            # the ticks per simulated second
            maxtick_from_rel += cpt_starttick
            if options.at_instruction or options.simpoint:
                warn(
                    "Relative max tick specified with --at-instruction or"
                    " --simpoint\n      These options don't specify the "
                    "checkpoint start tick, so assuming\n      you mean "
                    "absolute max tick"
                )
        explicit_maxticks += 1
    if options.maxtime:
        maxtick_from_maxtime = m5.ticks.fromSeconds(options.maxtime)
        explicit_maxticks += 1
    if explicit_maxticks > 1:
        warn(
            "Specified multiple of --abs-max-tick, --rel-max-tick, --maxtime."
            " Using least"
        )
    maxtick = min([maxtick_from_abs, maxtick_from_rel, maxtick_from_maxtime])

    print("**** REAL SIMULATION ****")

    # For se.y (only one simulate here line 200) and fe.py (two simulate with one after workbigin to have maxtick)
    exit_event = m5.simulate(maxtick - m5.curTick())
    if exit_event.getCause() == "workbegin":
        m5.stats.reset()
        print("Switching CPUs")
        m5.switchCpus(testsys, switch_cpu_list)
        print("CPU Switch Success")
    # exit_event = m5.simulate()            
    m5.stats.dump()
    print(
        "Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause())
    )

    if exit_event.getCode() != 0:
        print("Simulated exit code not 0! Exit code is", exit_event.getCode())
