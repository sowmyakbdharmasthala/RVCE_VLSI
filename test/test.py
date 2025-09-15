# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

# tests/test_tt_um_axi8_lite_proc.py
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# Bit positions in ui_in (matches your pinout)
UI_AWVALID = 0
UI_ARVALID = 1
UI_WVALID  = 2
UI_RREADY  = 3
UI_BREADY  = 4
UI_ADDR    = 5
UI_WSTRB   = 6
# UI[7] unused

def pack_ui(aw=0, ar=0, w=0, rr=1, br=1, addr=0, wstrb=1):
    """Compose ui_in value from individual control bits."""
    v  = (aw & 1) << UI_AWVALID
    v |= (ar & 1) << UI_ARVALID
    v |= (w  & 1) << UI_WVALID
    v |= (rr & 1) << UI_RREADY
    v |= (br & 1) << UI_BREADY
    v |= (addr & 1) << UI_ADDR
    v |= (wstrb & 1) << UI_WSTRB
    return v

async def reset_dut(dut):
    dut.ena.value   = 0
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    dut.ena.value   = 1
    await ClockCycles(dut.clk, 2)

async def axi_write(dut, addr: int, data: int):
    """Perform simplified single-beat AXI-Lite write:
       1) AWVALID handshake, then 2) WVALID handshake, BREADY held high."""
    # Put data on write bus
    dut.uio_in.value = data & 0xFF

    # Step 1: address phase
    dut.ui_in.value = pack_ui(aw=1, ar=0, w=0, rr=1, br=1, addr=addr, wstrb=1)
    await RisingEdge(dut.clk)
    # Wait for AWREADY (uo_out[0])
    while dut.uo_out[0].value.integer == 0:
        await RisingEdge(dut.clk)
    # Drop AWVALID
    dut.ui_in.value = pack_ui(aw=0, ar=0, w=0, rr=1, br=1, addr=addr, wstrb=1)

    # Step 2: data phase
    dut.ui_in.value = pack_ui(aw=0, ar=0, w=1, rr=1, br=1, addr=addr, wstrb=1)
    await RisingEdge(dut.clk)
    # Wait for WREADY (uo_out[1])
    while dut.uo_out[1].value.integer == 0:
        await RisingEdge(dut.clk)
    # Drop WVALID
    dut.ui_in.value = pack_ui(aw=0, ar=0, w=0, rr=1, br=1, addr=addr, wstrb=1)

    # Step 3: write response (BVALID on uo_out[2], BREADY already 1)
    await RisingEdge(dut.clk)
    while dut.uo_out[2].value.integer == 0:
        await RisingEdge(dut.clk)
    # One extra cycle for response acceptance
    await RisingEdge(dut.clk)

async def axi_read(dut, addr: int) -> int:
    """Perform simplified single-beat AXI-Lite read:
       ARVALID handshake, then capture data when RVALID, RREADY held high."""
    # Assert ARVALID
    dut.ui_in.value = pack_ui(aw=0, ar=1, w=0, rr=1, br=1, addr=addr, wstrb=1)
    await RisingEdge(dut.clk)
    # Wait for ARREADY (uo_out[3])
    while dut.uo_out[3].value.integer == 0:
        await RisingEdge(dut.clk)
    # Drop ARVALID
    dut.ui_in.value = pack_ui(aw=0, ar=0, w=0, rr=1, br=1, addr=addr, wstrb=1)

    # Wait for RVALID (uo_out[4]); DUT drives uio_out and uio_oe
    await RisingEdge(dut.clk)
    while dut.uo_out[4].value.integer == 0:
        await RisingEdge(dut.clk)

    # Check that the DUT is driving the bus
    assert dut.uio_oe.value.integer == 0xFF, "uio_oe must be 0xFF during read data"
    data = int(dut.uio_out.value) & 0xFF

    # Keep RREADY=1 so handshake completes next edge
    await RisingEdge(dut.clk)
    return data

@cocotb.test()
async def test_byte_invert(dut):
    """Write a byte to addr=0, expect bitwise-inverted byte at addr=1."""
    # 25 MHz clock (matches info.yaml clock_hz suggestion)
    cocotb.start_soon(Clock(dut.clk, 40, units="ns").start())

    await reset_dut(dut)

    test_val = 0x5A
    expected = (~test_val) & 0xFF

    # Write to address 0 (input reg -> processes into reg_out)
    await axi_write(dut, addr=0, data=test_val)

    # Read back from address 1 (processed output reg)
    got = await axi_read(dut, addr=1)

    assert got == expected, f"Mismatch: got 0x{got:02X}, expected 0x{expected:02X}"
