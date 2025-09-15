`timescale 1ns/1ps

module tb_tt_um_simple_echo;

    // Testbench signals
    reg  [7:0] ui_in;
    wire [7:0] uo_out;
    reg  [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
    reg        ena;
    reg        clk;
    reg        rst_n;

    // Instantiate DUT
    tt_um_simple_echo dut (
        .ui_in  (ui_in),
        .uo_out (uo_out),
        .uio_in (uio_in),
        .uio_out(uio_out),
        .uio_oe (uio_oe),
        .ena    (ena),
        .clk    (clk),
        .rst_n  (rst_n)
    );

    // Clock generation: 25 MHz (40 ns period)
    initial clk = 0;
    always #20 clk = ~clk;

    // Test procedure
    initial begin
        // VCD dump for waveform viewing
        $dumpfile("tb_tt_um_simple_echo.vcd");
        $dumpvars(0, tb_tt_um_simple_echo);

        // Initialize
        ui_in  = 8'h00;
        uio_in = 8'h00;
        ena    = 0;
        rst_n  = 0;

        // Reset sequence
        #100;
        rst_n = 1;
        ena   = 1;

        // Apply test patterns
        apply_test(8'h00);
        apply_test(8'hFF);
        apply_test(8'h55);
        apply_test(8'hAA);

        // Random tests
        repeat (5) begin
            apply_test($random);
        end

        // Disable design
        ena = 0;
        ui_in = 8'hAB;
        #50;
        if (uo_out !== 8'h00) $display("ERROR: uo_out not zero when ena=0!");

        $display("All tests completed.");
        $finish;
    end

    task apply_test(input [7:0] val);
    begin
        ui_in = val;
        #40;  // wait one clock
        if (uo_out !== val) begin
            $display("ERROR: Echo failed. ui_in=%h uo_out=%h", val, uo_out);
        end else begin
            $display("PASS: ui_in=%h uo_out=%h", val, uo_out);
        end
    end
    endtask

endmodule
