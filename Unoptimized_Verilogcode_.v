/*
This is the unoptimized version of a 4:1 MUX
After turning the Vivado Optimizer off
The result was 9 LUTs
However algorithim gave just 7 LUTs
*/
(* DONT_TOUCH = "true" *)
module Direct_Result(
    input  wire [3:0] D,
    input  wire [1:0] S,
    output wire       Y
);
    // Decode select signals
    (* keep = "true" *) wire S0 = S[0];
    (* keep = "true" *) wire S1 = S[1];

    (* keep = "true" *) wire nS0 = ~S0;
    (* keep = "true" *) wire nS1 = ~S1;

    // Product terms (like your and1..and4)
    (* keep = "true" *) wire t0 = nS1 & nS0 & D[0];  // and1
    (* keep = "true" *) wire t1 = nS1 &  S0 & D[1];  // and2
    (* keep = "true" *) wire t2 =  S1 & nS0 & D[2];  // and3
    (* keep = "true" *) wire t3 =  S1 &  S0 & D[3];  // and4

    // OR tree (or1, or2, or3)
    (* keep = "true" *) wire w0 = t0 | t1;
    (* keep = "true" *) wire w1 = t2 | t3;
    (* keep = "true" *) assign Y = w0 | w1;

endmodule
