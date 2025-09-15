# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

# tests/test_tt_um_simple_echo.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles
import random

async def reset_dut(dut):
    """Reset the DUT"""
    dut.ena.value = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    dut.ena.value = 1
    await ClockCycles(dut.clk, 2)

@cocotb.test()
async def test_echo(dut):
    """Check that ui_in is echoed to uo_out when ena=1"""
    # Start a clock (25 MHz → 40 ns period)
    cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

    await reset_dut(dut)

    # Test a few static values
    for val in [0x00, 0x55, 0xAA, 0xFF]:
        dut.ui_in.value = val
        await RisingEdge(dut.clk)
        got = int(dut.uo_out.value)
        assert got == val, f"Echo failed: ui_in={val:02X}, uo_out={got:02X}"

    # Test with random patterns
    for _ in range(10):
        val = random.randint(0, 255)
        dut.ui_in.value = val
        await RisingEdge(dut.clk)
        got = int(dut.uo_out.value)
        assert got == val, f"Echo failed: ui_in={val:02X}, uo_out={got:02X}"

@cocotb.test()
async def test_disabled_output(dut):
    """Check that outputs are forced to 0 when ena=0"""
    # Start a clock
    cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

    await reset_dut(dut)

    # Disable design
    dut.ena.value = 0
    dut.ui_in.value = 0xAB
    await RisingEdge(dut.clk)

    got = int(dut.uo_out.value)
    assert got == 0, f"With ena=0, uo_out should be 0 but got {got:02X}"
