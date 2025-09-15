/*
 * Simple Tiny Tapeout Example
 * Echo inputs to outputs
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_simple_echo (
    input  wire [7:0] ui_in,    // 8 dedicated inputs
    output wire [7:0] uo_out,   // 8 dedicated outputs
    input  wire [7:0] uio_in,   // unused bidir inputs
    output wire [7:0] uio_out,  // unused bidir outputs
    output wire [7:0] uio_oe,   // unused bidir enables
    input  wire       ena,      // design enable
    input  wire       clk,      // clock
    input  wire       rst_n     // async reset (active low)
);

    // Just loop inputs to outputs when enabled
    assign uo_out = ena ? ui_in : 8'h00;

    // Not using bidirectional IOs
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;

endmodule
