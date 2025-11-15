`timescale 1ns / 1ps

module tb() ;

wire Ydr,Yop;  ///direct output, optimized output
reg [3:0] D;
reg [1:0] S;
reg clk;

initial clk = 0;
always #5 clk = ~clk;

Direct_Result dr1(.D(D), .S(S), .Y(Ydr));
Optimized_MUX mu1(.D(D), .S(S), .Y(Yop));

always @(posedge clk) begin

D <= 4'b0110;
S <= 2'b00;

#10 //wait 1 clk cycle
S <= 2'b01;

#10 //wait 1 clk cycle
S <= 2'b10;

#10 //wait 1 clk cycle
S <= 2'b11;

#10
$stop ;
end
endmodule
